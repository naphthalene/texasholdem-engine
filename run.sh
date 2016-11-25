#! /bin/bash

if [ "$#" -ne 2 ]; then
  echo "Please pass arguments: bot1, bot2"
  echo "./compile_bot.sh <starterBot> <myBot>"
  exit 1
fi

echo "Don't forget to recompile"
echo
echo

java -cp bin com.theaigames.game.texasHoldem.TexasHoldem "java -cp $1/bin/ bot.BotStarter" "java -cp $2/bin/ bot.BotStarter"
