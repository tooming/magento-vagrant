from fabric.api import *
from fabric.contrib import files


def vagrant():
    """Set env to local vagrant."""
    env.name = 'vagrant'
    env.hostname = 'magento'
    env.user = 'ubuntu'
    env.key_filename = '.vagrant/machines/magento/virtualbox/private_key'
    env.hosts = ['192.168.56.206']
    env.sites = ['local-magento-com']  # sites from config/etc/nginx/sites-enabled to enable


def provision():
    """Provision the server."""
    sudo('hostnamectl set-hostname %s' % env.hostname)
    files.append('/etc/hosts', "127.0.0.1 magento", use_sudo=True)

    sudo("apt-get update")
    applications = [
        'htop', 'nginx', 'php-fpm', 'mysql-server', 'unzip',
        'php-dom', 'php-curl', 'php-gd', 'php-mcrypt', 'php-soap',  # for magento
        'php-intl', 'php-mbstring', 'php-mysql', 'php-zip', 'php-bcmath'  # for magento
    ]
    debconf_set_selection("mysql-server mysql-server/root_password password root")
    debconf_set_selection("mysql-server mysql-server/root_password_again password root")
    for application in applications:
        sudo("apt-get -y install %s" % application)

    # symlink nginx conf
    for site in env.sites:
        sudo('ln -sfn /var/www/html/%(site)s.conf'
             ' /etc/nginx/sites-enabled/%(site)s.conf' % {'site': site})

    # configure nginx
    with settings(warn_only=True):
        sudo('rm /etc/nginx/sites-enabled/default')
    with settings(warn_only=True):
        sudo('rm /var/www/html/index.nginx-debian.html')
    files.sed('/etc/nginx/nginx.conf',
              'user www-data;',
              'user ubuntu;',
              use_sudo=True)

    # configure php
    files.sed('/etc/php/7.0/fpm/pool.d/www.conf',
              'user = www-data',
              'user = ubuntu',
              use_sudo=True)
    files.sed('/etc/php/7.0/fpm/pool.d/www.conf',
              'listen.owner = www-data',
              'listen.owner = ubuntu',
              use_sudo=True)

    # install composer
    sudo('curl -sS https://getcomposer.org/installer | '
         'sudo php -- --install-dir=/usr/local/bin --filename=composer')

    # download magento
    if not files.exists('/var/www/html/magento'):
        with cd('/var/www/html'):
            run('curl https://github.com/magento/magento2/archive/2.2-develop.zip '
                '-L -o magento2.zip')
            run('unzip magento2.zip')
            run('mv magento2-2.2-develop magento')

    # install composer stuff (is it necessary?)
    with cd('/var/www/html/magento'):
        run('composer install')

    # add db
    grant_priv = "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'root';" \
        " FLUSH PRIVILEGES;"
    run('mysql -u root -proot -e "{}"'.format(grant_priv))
    mysql_create_db('magento2')
    files.sed('/etc/mysql/mysql.conf.d/mysqld.cnf',
              'bind-address.*$',
              'bind-address=0.0.0.0',
              use_sudo=True)

    # install phpmyadmin
    with shell_env(DEBIAN_FRONTEND="noninteractive"):
        sudo("apt-get -y install phpmyadmin")
    sudo('ln -sfn /usr/share/phpmyadmin /var/www/html/phpmyadmin')
    files.append('/etc/phpmyadmin/conf.d/send-error-reports.php',
                 "<?php $cfg['SendErrorReports'] = 'never';", use_sudo=True)

    # install magento
    run('/var/www/html/magento/bin/magento setup:install '
        '--admin-user admin --admin-firstname admin '
        '--admin-lastname admin --admin-email admin@magento.com --admin-password admin123 '
        '--db-password root --backend-frontname admin')

    sudo("service nginx restart")
    sudo("service php7.0-fpm restart")
    sudo("service mysql restart")


def debconf_set_selection(conf):
    sudo('debconf-set-selections <<< "%s"' % conf)


def mysql_create_db(name):
    """Create MySQL stuff."""
    create_db = "CREATE DATABASE IF NOT EXISTS `{}`;".format(name)
    run("mysql -u root -proot -e '{}'".format(create_db))
