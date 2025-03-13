Vagrant.configure("2") do |config|
  # VM1 - Servidor Web (Python)
  config.vm.define "web" do |web|
    web.vm.box = "ubuntu/jammy64"
    web.vm.hostname = "webserver"
    web.vm.network "private_network", ip: "192.168.56.10"
    web.vm.provider 'virtualbox' do |vb|
      vb.memory = "1024"
      vb.cpus = 1
    end
    web.vm.synced_folder "./app", "/home/vagrant/app"
    web.vm.provision "shell", inline: <<-SHELL
      echo "Instalando Python..."
      sudo apt update
      sudo apt install -y python3 python3-pip
      
      echo "Instalando o Flask..."
      pip3 install flask
      
      echo "Verificando a instalação..."
      python3 --version
      pip3 --version
      
      # Executando o servidor Python (Flask)
      echo "Iniciando o servidor Flask..."
      cd /home/vagrant/app
      nohup python3 app.py &
    SHELL
  end

  # VM2 - Servidor Banco de Dados Mysql com Firewall
  config.vm.define "db" do |db|
    db.vm.box = "ubuntu/jammy64"
    db.vm.hostname = "dbserver"
    db.vm.network "private_network", ip: "192.168.56.20"
    db.vm.provider 'virtualbox' do |vb|
      vb.memory = "1024"
      vb.cpus = 1
    end
    db.vm.provision "shell", inline: <<-SHELL
      echo "Instalando MySQL..."
      sudo apt update
      sudo apt install -y mysql-server
      echo "Configurando o Firewall..."
      sudo ufw allow mysql
      sudo ufw enable
      echo "Verificando o status do MySQL..."
      sudo systemctl status mysql
    SHELL
  end
end
