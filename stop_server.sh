#!/bin/bash

if ! screen -list | grep -q "minecraft"; then
    echo "Ошибка: Сервер не запущен."
    exit 1
fi

echo "Отправка команды остановки..."
screen -S minecraft -p 0 -X stuff "say Сервер выключается...^M"
sleep 2
screen -S minecraft -p 0 -X stuff "stop^M"

echo "Ожидание завершения..."
while screen -list | grep -q "minecraft"; do
    sleep 1
done

echo "Сервер VortexNode остановлен."

