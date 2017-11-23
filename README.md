# TG s Bot 

Requierments: 
* redis >= 4.0


Для начала зарегестрируйте нового бота через @BotFather в телеграме и получите для него Token.
Не забудьте выключить возможность добавления бота в группу.

## Запуск бота
Бот предоставляет хелпер для работы через СLI: `tgbot.cli`. Т.к. конфигурация бота хранится в redis для того что бы можно было запускать можноство инстансов синхронизируемых между собой, необходимо указать хост с базой redis и базу cм. пример.
```
tgbot.cli --redis redis://redis.gening.name --redis-db 11 run --token "478146475:AAGHBTMpOr8ErBp7xduSZjuLwKP5cYmox7w"

```
 

## Проверка конфига
CLI интерфейс предоставляет отдельную команду для проверки конфигурации бота. 
Эту команду можно использовать как чеклист установки бота с новым редисом.
Обратите внимание что множество инстаносов бота будут использовать один и тот же конфиг, т.к. он храниться в ключе редиса.

```
tgbot.cli --redis redis://redis.gening.name --redis-db 11 config
```

## Авторизация через Google OAuth2

Бот авторизуеся через Google OAuth от лица определенного пользователя для того что бы получать обновления Google Sheets

Для авториацзии требуется получить приватный ключ приложения от Google в формате JSON. Его можно получить через Google Cloud Console: https://console.cloud.google.com
Создайте новое приложение и добавьте ему доступ к API Google Sheeet и Google Drive. Затем создайте ключ идентификатор клиентa OAuth 2.0 c типом "Другие Типы" и скачайте секретный ключ в формате JSON. В примере ниже полученный JSON называется secret.json и находится в текущей папке
```
tgbot.cli --redis redis://<redis host>:<redis port> --redis-db <redis db> adm oauth --secret secret.json
```
Пройдите по сгененированной ссылке и получите токен OAuth2 для пользователя от лица которого будут скачиватсья Google Sheet.
Проверить что авторизация успешно прошла можно используая команду config.

## Установка и первоначальное скачиваение Google Sheet
Запустите следующую команду:
```
tgbot.cli --redis redis://<redis host>:<redis port> --redis-db <redis db> adm <google sheet url>
```
Идентификатор Google Sheet сохранится и будет использован для атоматического обновления. Для того что бы вручную обновить базу из Google Sheet прямо сейчас используйте флаг `--force`


# Использование Docker
Для того что бы не использовать кастомные способы демонизации процесса бота можно запустить
используя docker.

## Запуск 
```sh
docker build -t tgbot .
docker run -d tgbot tgbot.cli --redis redis://redis.gening.name --redis-db 11 \
  run --token "478146475:AAGHBTMpOr8ErBp7xduSZjuLwKP5cYmox7w"
```

## Выполнение команд CLI интерфейса
```
docker run --rm -it tgbot tgbot.cli --redis redis://redis.gening.name --redis-db 11 config
```

## Запуск через docker-compose (тестовый режим)
В репозитории есть docker-compose файл который облегчает запуск для тестов и разработки. Он так же поднимает redis сервис.

*NB:* В виду особенности файловой системы докера исполняемый файл tgbot.cli может быть не доступен. 
Используйте запуск через `python -m tgbot.entrypoint`

```
echo TG_TOKEN=<telegram bot token> > .env
docker-compose up
docker-compose exec tgbot python -m tgbot.entrypoint config
```


