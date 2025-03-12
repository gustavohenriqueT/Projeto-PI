Vagrant.configure("2") do |config|
  #VM1 - servidor web (Node.js)
    config.vm.define "web" do |web|
      web.vm.box = "ubuntu/jammy64"
      web.vm.hostname = "webserver"
      web.vm.network "private_network", type: "dhcp"
      web.vm.provider 'vitrualbox' do |vb|
        vb.memory = "1024"
        vb.cpus = 1
      end
    web.vm.provision 'shell', inline: <<-SHELL
      sudo apt update 
      sudo apt install -y apache2 
      sudo systemctl enable apache2
      sudo systemctl start apache2
      SHELL
    end  
  end