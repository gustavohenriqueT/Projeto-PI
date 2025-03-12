Vagrant.configure("2") do |config|
  #VM1 - servidor web (Node.js)
    config.vm.define "web" do |web|
      web.vm.box = "ubuntu/jammy64"
      web.vm.hostname = "webserver"
      web.vm.network "private_network", ip:"192.168.56.10"
      web.vm.provider 'vitrualbox' do |vb|
        vb.memory = "1024"
        vb.cpus = 1
      end
      web.vm.synced_folder "./app", "home/vagrant/app"
      web.vm.provision "shell", inline: <<-SHELL
        echo "atualizando pacotes..."
        sudo apt -y
        echo "instalando dependencias..."
        sudo apt install -y curl
        echo "instalando node..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
        \. "$HOME/.nvm/nvm.sh"
        vm install 22
        echo "verificar instalação..."
        mode -v
        npm -v
      SHELL
    end
  #VM2 - Servidor Banco de Dados Mysql com Firewall
    #config.vm.define 'db' do |db|
  end

