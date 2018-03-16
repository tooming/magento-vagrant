# -*- mode: ruby -*-
# vi: set ft=ruby :

ip = "192.168.56.206"

if ARGV[0] == 'up' or ARGV[0] == 'reload'
  puts "==> You are doing vagrant #{ARGV[0]} and therefore we clear #{ip} from known_hosts"
  system("ssh-keygen -R #{ip}")
end

Vagrant.configure 2 do |global_config|
    global_config.vm.define :magento do |config|
        config.vm.provider :virtualbox do |v|
            v.gui = false
            v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
        end

        config.vm.box = 'ubuntu/xenial64'
        config.vm.guest = :ubuntu
        config.vm.hostname = "local.magento.com"
        config.vm.network "private_network", ip: "#{ip}"
        config.hostsupdater.aliases  = %w{local-pma.magento.com}

        config.vm.synced_folder ".", "/var/www/html", mount_options: ["dmode=775"]

        config.vm.provision :shell do |shell|
              shell.inline = <<-SHELL
        echo "\e[33mrun 'fab vagrant provision'"
        echo "\e[33mAdd local.magento.com into hosts file on your HOST machine with ip = 192.168.56.206"
        echo "\e[33mNow go to local.magento.com and see the excellence!"
              SHELL
        end
    end
end
