#!/bin/bash

# Путь к файлу конфигурации
CONFIG_FILE="server.conf"

# Функция для чтения значений из server.conf
get_config_id() {
    grep "^$1=" "$CONFIG_FILE" | cut -d'=' -f2
}

# Проверяем, существует ли конфиг
if [ ! -f "$CONFIG_FILE" ]; then
    echo "--- [!] ОШИБКА: server.conf не найден! ---"
    exit 1
fi

# Загружаем переменные из конфига
JAR_NAME=$(get_config_id "jar")
RAM_SIZE=$(get_config_id "ram")
JAVA_VER=$(get_config_id "java")

# Вывод информации о запуске
echo "--- VortexNode Boot ---"
echo "Ядро: $JAR_NAME"
echo "Java: $JAVA_VER"
echo "Память: $RAM_SIZE"
echo "-----------------------"

# Проверка наличия файла ядра
if [ ! -f "$JAR_NAME" ]; then
    echo "--- [!] ОШИБКА: Файл $JAR_NAME не найден! Сначала скачайте ядро. ---"
    exit 1
fi

# Исправление ошибки "java17 не найдено"
# Если в конфиге указано java17, java11 и т.д., но такой команды нет, используем системную java
if command -v "$JAVA_VER" >/dev/null 2>&1; then
    JAVA_CMD="$JAVA_VER"
else
    echo "--- [!] Предупреждение: команда $JAVA_VER не найдена, использую системную java ---"
    JAVA_CMD="java"
fi

# Запуск сервера
# -Xms и -Xmx устанавливают ОЗУ из конфига
# nogui отключает графический интерфейс для экономии ресурсов телефона
$JAVA_CMD -Xms$RAM_SIZE -Xmx$RAM_SIZE -jar $JAR_NAME nogui

echo "--- Сервер остановлен ---"

