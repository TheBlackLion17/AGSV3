#!/bin/bash

# Update & upgrade system
apt update && apt upgrade -y
apt install -y git python3 python3-venv python3-pip tmux

# Clone the repo 
if [ -z $UPSTREAM_REPO ]; then
    echo "Cloning main Repository"
    git clone https://github.com/TheBlackLion17/AADVAN_VPS /AADVAN_VPS
else
    echo "Cloning Custom Repo from $UPSTREAM_REPO"
    git clone $UPSTREAM_REPO /AADVAN_VPS
fi

# Create and activate virtual environment
cd /ProfessorBot
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install requirements
pip install -U pip
pip install -U -r requirements.txt --force-reinstall

# Start bot in a tmux session
echo "Starting Bot in tmux session 'bot'....✨"
tmux new-session -d -s professorbot 'source venv/bin/activate && python3 bot.py'
echo "Bot is running inside tmux. Use: tmux attach -t bot"
