import re
from StringIO import StringIO
import string

from fabric import colors
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.utils import indent

from django.utils.crypto import get_random_string


"""
    Usage:
        fab TARGET actions

    Actions:
        simple_deploy # Deploy updates without migrations.
            :arg id Identifier to pass to hg update command.
            :arg silent If true doesn't show confirms.

        offline_deploy # Deploy updates with migrations with server restart.
            :arg id Identifier to pass to hg update command.
            :arg silent If true doesn't show confirms.

        online_deploy # Deploy updates with migrations without server restart.
            :arg id Identifier to pass to hg update command.
            :arg silent If true doesn't show confirms.

        version # Get the version deployed to target.
        update_requirements # Perform pip install -r requirements/production.txt

        stop_server # Stop the remote server service.
        start_server # Start the remote server service.
        restart_server # Restart the remote server service.

        migrate_diff # Get the status of migrations needed when upgrading target to the specified version.
            :arg id Identifier of revision to check against.
"""


PRODUCTION_LOCAL_SETTINGS = """from settings.production import *

SECRET_KEY = '${secret_key}'

DATABASES = {
    'default': {
        'ENGINE':'django.db.backends.postgresql_psycopg2',
        'NAME': 'realtimedemo',
        'USER': 'realtimedemo',
        'PASSWORD': '${db_password}',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
"""


""" TARGETS """

# Use  .ssh/config  so that you can use hosts defined there.
env.use_ssh_config = True

def defaults():
    env.venv_name = 'venv'
    env.confirm_required=True
    env.code_dir = '/'
    env.hg_extra = ''

@task
def live():
    defaults()
    env.hosts = ['fiesta.thorgate.eu']
    env.tag = 'realtimedemo-live'
    env.service_name = "gunicorn-realtimedemo"

    env.code_dir = '/srv/realtimedemo'


""" FUNCTIONS """

@task
def show_log(id=None):
    """ List revisions to apply/unapply when updating to given revision.
        When no revision is given, it default to the head of current branch.
        Returns False when there is nothing to apply/unapply. otherwise revset of revisions that will be applied or
        unapplied (this can be passed to  hg status  to see which files changed for example).
    """
    require('code_dir')

    def run_hg_log(revset):
        """ Returns lines returned by hg log, as a list (one revision per line). """
        result = sudo("hg log --template '{rev}:{node|short} {branch} {desc|firstline}\\n' -r '%s'" % revset)
        return result.split('\n') if result else []

    def get_revset(x, y):
        assert x or y
        if x and y:
            # All revisions that are descendants of the current revision and ancestors of the target revision
            #  (inclusive), but not the current revision itself
            return '%s::%s' % (x, y)
        else:
            # All revisions that are in the current branch, are descendants of the current revision and are not the
            #  current revision itself.
            return 'branch(p1()) and %s::%s' % (x or '', y or '')

    with cd(env.code_dir), hide('running', 'stdout'):
        # First do hg pull
        hg_pull()

        revset = get_revset('.', id)
        revisions = run_hg_log(revset)

        if len(revisions) > 1:
            # Target is forward of the current rev
            print "Revisions to apply:"
            print indent(revisions[1:])
            return revset
        elif len(revisions) == 1:
            # Current rev is the same as target
            print "Already at target revision"
            return False

        # Check if target is backwards of the current rev
        revset = get_revset(id, '.')
        revisions = run_hg_log(revset)
        if revisions:
            print "Revisions to _un_apply:"
            print indent(reversed(revisions[1:]))
            return revset
        else:
            print "Target revision is not related to the current revision"
            return False


@task
def migrate_diff(id=None, revset=None, silent=False):
    """ Check for migrations needed when updating to the given revision. """
    require('code_dir')

    # Exactly one of id and revset must be given
    assert id or revset
    assert not (id and revset)
    if not revset:
        revset = '.::%s' % id

    migrations = changed_files(revset, "\/(?P<model>\w+)\/migrations\/(?P<migration>.+)")

    if not silent and migrations:
        print "Found %d migrations." % len(migrations)
        print indent(migrations)

    return migrations


@task
def update_requirements(reqs_type='production'):
    """ Install the required packages from the requirements file using pip """
    require('hosts')
    require('code_dir')

    with cd(env.code_dir), prefix('. venv/bin/activate'):
        sudo('pip install -r requirements/%s.txt' % reqs_type)

def migrate(silent=False):
    """ Preform migrations on the database. """

    if not silent:
        request_confirm("migrate")

    management_cmd("migrate --noinput")

@task
def version():
    """ Get current target version hash. """
    require('hosts')
    require('code_dir')
    require('tag')

    with cd(env.code_dir),  hide('running'):
        result = run("hg id -nib", quiet=True)
        print "Target %s version: %s" % (env.tag, colors.yellow(result))

@task
def deploy(id=None, silent=False):
    """ Perform an automatic deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    # See if we have any requirements changes
    requirements_changes = changed_files(revset, r' requirements/')
    if requirements_changes:
        print colors.yellow("Will update requirements (and do migrations):")
        print indent(requirements_changes)

    # See if we have any changes to migrations between the revisions we're applying
    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        print colors.yellow("Will apply %d migrations:" % len(migrations))
        print indent(migrations)

    if not silent:
        request_confirm("deploy")

    hg_update(id)
    if requirements_changes:
        update_requirements()
    if migrations or requirements_changes:
        migrate(silent=True)
    collectstatic()
    restart_server(silent=True)

@task
def simple_deploy(id=None, silent=False):
    """ Perform a simple deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        msg = "Found %d migrations; are you sure you want to continue with simple deploy?" % len(migrations)
        if not confirm(colors.yellow(msg), False):
            abort('Deployment aborted.')

    if not silent:
        request_confirm("simple_deploy")

    hg_update(id)
    collectstatic()
    restart_server(silent=True)

@task
def online_deploy(id=None, silent=False):
    """ Perform an online deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        print colors.yellow("Will apply %d migrations:" % len(migrations))
        print indent(migrations)

    if not silent:
        request_confirm("online_deploy")

    hg_update(id)
    migrate(silent=True)
    collectstatic()
    restart_server(silent=True)

@task
def offline_deploy(id=None, silent=False):
    """ Perform an offline deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        print colors.yellow("Will apply %d migrations:" % len(migrations))
        print indent(migrations)

    if not silent:
        request_confirm("offline_deploy")

    stop_server(silent=True)
    hg_update(id)
    migrate(silent=True)
    collectstatic()
    start_server(silent=True)


@task
def setup_server():
    require('hosts')
    require('code_dir')

    # Clone code repository
    hg_url = local('hg paths default', capture=True)
    assert hg_url
    sudo('hg clone %s %s' % (hg_url, env.code_dir))

    # Create password for DB, secret key and the local settings
    db_password = generate_password()
    secret_key = generate_password()
    local_settings = string.Template(PRODUCTION_LOCAL_SETTINGS).substitute(db_password=db_password, secret_key=secret_key)

    # Create database
    sudo('echo "CREATE DATABASE realtimedemo; '
               'CREATE USER realtimedemo WITH password \'%s\'; '
               'GRANT ALL PRIVILEGES ON DATABASE realtimedemo to realtimedemo;" '
         '| su -c psql postgres' % db_password)

    # Create virtualenv and install dependencies
    with cd(env.code_dir):
        sudo('virtualenv -p python3.4 venv')
    update_requirements()

    # Upload local settings
    put(local_path=StringIO(local_settings), remote_path=env.code_dir + '/realtimedemo/settings/local.py', use_sudo=True)

    # Create necessary dirs, with correct permissions
    mkdir_wwwdata('/var/log/realtimedemo/')
    with cd(env.code_dir + '/realtimedemo'), prefix('. ../venv/bin/activate'):
        mkdir_wwwdata('assets/CACHE/')
        mkdir_wwwdata('media/')

    # syncdb, migrations, collectstatic
    management_cmd('syncdb')
    management_cmd('migrate')
    collectstatic()

    # Ensure any and all created log files are owned by the www-data user
    sudo('chown -R www-data:www-data /var/log/realtimedemo/')

    # Copy nginx and gunicorn confs
    with cd(env.code_dir):
        sudo('cp deploy/nginx.conf /etc/nginx/sites-enabled/realtimedemo')
        sudo('cp deploy/gunicorn.conf /etc/init/gunicorn-realtimedemo.conf')

    # (Re)start services
    start_server(silent=True)
    sudo('service nginx restart')


""" SERVER COMMANDS """
def stop_server(silent=False):
    if not silent:
        request_confirm("stop_server")

    require('service_name')
    sudo("service %s stop" % env.service_name)

def start_server(silent=False):
    if not silent:
        request_confirm("start_server")

    require('service_name')
    sudo("service %s start" % env.service_name)

def restart_server(silent=False):
    if not silent:
        request_confirm("restart_server")

    require('service_name')
    sudo("service %s restart" % env.service_name)

""" HELPERS """
@task
def management_cmd(cmd):
    """ Preform a management command on the target. """

    require('hosts')
    require('code_dir')

    sudo("cd %s ;"
         ". ./venv/bin/activate ; "
         "cd realtimedemo ; "
         "python manage.py %s" % (env.code_dir, cmd))

def hg_pull():
    with cd(env.code_dir):
        sudo("hg pull %(hg_extra)s" % {
            "hg_extra": env.hg_extra,
        })

def hg_update(revision=''):
    with cd(env.code_dir):
        sudo("hg update %(rev)s" % {
            "rev": revision if revision else '',
        })


def changed_files(revset, filter_re=None):
    """
    Returns list of files that changed in the given revset, optionally filtered by the given regex.
    """
    require('code_dir')

    with cd(env.code_dir):
        result = run("hg status --rev '%s'" % revset, quiet=True).splitlines()

        if filter_re:
            regex = re.compile(filter_re)
            result = filter(lambda filename: regex.search(filename), result)

        return result


def collectstatic():
    management_cmd('collectstatic --noinput')


def mkdir_wwwdata(path):
    # Creates directory and makes www-data its owner
    sudo('mkdir -p ' + path)
    sudo('chown www-data:www-data ' + path)


def request_confirm(tag):
    require('confirm_required')

    if env.confirm_required:
        if not confirm("Are you sure you want to run task: %s on servers %s?" % (tag, env.hosts)):
            abort('Deployment aborted.')


def generate_password(length=50):
    # Similar to Django's charset but avoids $ to avoid accidential shell variable expansion
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#%^&*(-_=+)'
    return get_random_string(length, chars)
