Vagrant.configure("2") do |config|
  #VM1 - servidor web (Node.js)
    config.vm.define "web" do |web|
      web.vm.box = "ubuntu/jammy64"
      web.vm.hostname = "webserver"
      web.vm.network "private_network", ip:"192.168.56.10"
      web.vm.provider 'virtualbox' do |vb|
        vb.memory = "1024"
        vb.cpus = 1
      end
      web.vm.synced_folder "./app", "/home/vagrant/app"
      web.vm.provision "shell", inline: <<-SHELL
        echo "instalando node..."
        sudo apt install -y nodejs 
        echo "verificar instalação..."
        node -v
        npm -v
      SHELL
    end
  #VM2 - Servidor Banco de Dados Mysql com Firewall
    #config.vm.define 'db' do |db|
  end

