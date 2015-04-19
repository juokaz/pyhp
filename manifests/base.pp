node default {
    # this makes puppet and vagrant shut up about the puppet group
    group { "puppet":
        ensure => "present",
    }

    # Set default paths
    Exec { path => '/usr/bin:/bin:/usr/sbin:/sbin' }

    # make sure the packages are up to date before beginning
        exec { "apt-get update":
        command => "apt-get update"
    }

    # because puppet command are not run sequentially, ensure that packages are
    # up to date before installing before installing packages, services, files, etc.
    Package { require => Exec["apt-get update"] }
    File { require => Exec["apt-get update"] }

    package {
        "build-essential": ensure => installed;
        "python3": ensure => installed;
        "python3-dev": ensure => installed;
        "python3-pip": ensure => installed;
    }

    exec{ "retrieve_pypy":
        command => "/usr/bin/wget -q https://bitbucket.org/pypy/pypy/downloads/pypy-2.5.1-linux64.tar.bz2 -O /home/vagrant/pypy.tar.bz2",
        creates => "/home/vagrant/pypy.tar.bz2",
    }

    file { "/home/vagrant/pypy":
        ensure => "directory",
        mode => 777,
    }

    exec { "extract_pypy":
        command => "tar xfv pypy.tar.bz2 -C pypy --strip-components 1",
        cwd => "/home/vagrant",
        creates => "/home/vagrant/pypy/bin",
        require => [File["/home/vagrant/pypy"], Exec["retrieve_pypy"]]
    }

    file { '/usr/local/bin/pypy':
        ensure => 'link',
        target => '/home/vagrant/pypy/bin/pypy',
        require => Exec["extract_pypy"]
    }

    exec { "retrieve_pypy-src":
        command => "/usr/bin/wget -q https://bitbucket.org/pypy/pypy/downloads/pypy-2.5.1-src.tar.bz2 -O /home/vagrant/pypy-src.tar.bz2",
        creates => "/home/vagrant/pypy-src.tar.bz2",
    }

    file {  "/home/vagrant/pypy-src":
        ensure => "directory",
        mode => 777,
    }

    exec { "extract_pypy-src":
        command => "tar xfv pypy-src.tar.bz2 -C pypy-src --strip-components 1",
        cwd => "/home/vagrant",
        creates => "/home/vagrant/pypy-src/pypy",
        require => [File["/home/vagrant/pypy-src"], Exec["retrieve_pypy-src"]]
    }

    file { '/usr/local/bin/rpython':
        ensure => 'link',
        target => '/home/vagrant/pypy-src/rpython/bin/rpython',
        require => Exec["extract_pypy-src"]
    }

    exec { "python-dependencies":
        command => "pip3 install -r requirements.txt",
        cwd => "/var/www/pyhp",
        require => Package["python3-pip"],
    }
}
