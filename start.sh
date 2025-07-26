apt update && apt upgrade -y

apt install git -y           
pip install -U pip  

if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/TheBlackLion17/AADVAN_VPS.git /AADVAN_VPS
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /AADVAN
fi
cd /AADVAN
pip3 install -U -r requirements.txt
echo "Starting Bot...."
python3 bot.py
