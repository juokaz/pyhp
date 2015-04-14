Vagrant::Config.run do |config|
  config.vm.box = "utopic"
  config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/utopic/current/utopic-server-cloudimg-amd64-vagrant-disk1.box"

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "manifests"
    puppet.manifest_file  = "base.pp"
  end

  config.vm.network :hostonly, "33.33.33.20"

  config.vm.share_folder "www", "/var/www/pyhp", "./", :nfs => true
end
