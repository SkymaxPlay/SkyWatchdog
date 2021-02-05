import subprocess

import requests
import wmi

from app.managers import mailmanager
from app.objects.task import Task
from app.objects.types import CheckType, PayloadType, JsonType

tasks = []


def setup(configuration):
    for task in configuration:
        try:
            tasks.append(parse_task(task))
        except Exception as e:
            print('Nie mozna sparsowac taska:', task.get("name", ""))
            print(e)


def parse_task(obj):
    name = obj.get("name")
    try:
        check_type = CheckType[(obj.get("checkType"))]
    except:
        raise Exception("Nieprawidlowy JsonType:", obj.get("checkType"))

    if check_type is None:
        raise Exception("Brak wsparcia dla tego typu sprawdzania")

    source = obj.get("source")
    task = Task(name, check_type, source)
    payload = obj.get("payload") if check_type == CheckType.ENDPOINT else None

    if payload is not None:
        payload_type = PayloadType[payload.get("type")]

        if payload_type is None:
            raise Exception("Brak wsparcia dla tego typu payloadu")

        payload["type"] = payload_type
        steps = payload.get("steps")

        if payload_type == PayloadType.JSON:
            if steps is None:
                raise Exception("Nie znaleziono krokow dla payloadu typu JSON")

            for step in steps:
                s_type = JsonType[step.get("type")]
                step["type"] = s_type

                if s_type == JsonType.JSON_ARRAY and not isinstance(step.get("object"), int):
                    raise Exception("object musi byc typu int jesli type jest JSON_ARRAY")

        expects = payload.get("expects")

        if expects is None:
            raise Exception("payload nie posiada elementu 'expects'")

        task.payload = payload

    if task.payload is None and check_type == CheckType.ENDPOINT:
        raise Exception("Nie znaleziono konfiguracji payload")

    rescue_exec = obj.get("rescue-exec")
    notify = obj.get("notify")

    task.rescue_exec = rescue_exec
    task.notify = notify

    return task


def check():
    w = wmi.WMI()

    for task in tasks:
        if task.check_type == CheckType.PROCESS:
            found = False

            for process in w.Win32_Process():
                if process.Name == task.source:
                    found = True
                    break

            process_verify_task(task, found)

            task.last_check_good = found

        elif task.check_type == CheckType.ENDPOINT:
            ok = False

            try:
                response = requests.get(task.source)
            except Exception:
                process_verify_task(task, ok)
                task.last_check_good = ok

                continue

            payload = task.payload
            p_type = payload.get("type")
            expects = payload.get("expects")

            if p_type == PayloadType.PLAIN:
                ok = expects == response.text
                print("OK:", ok, "PLAIN:", response.text)

            elif p_type == PayloadType.JSON:
                json = response.json()

                for step in payload.get("steps"):
                    s_type = step.get("type")
                    obj = step.get("object")

                    if s_type == JsonType.JSON_ARRAY:
                        json = json[obj]
                    elif s_type == JsonType.JSON_OBJECT:
                        json = json[obj]

                ok = json == expects
                print("OK:", ok, "JOIN: ", response.json())

            process_verify_task(task, ok)

            task.last_check_good = ok


def process_verify_task(task: Task, verify_result):
    if not verify_result and task.last_check_good:
        if task.notify.get("on-error"):
            mailmanager.send_notify_mail(task)

        if task.rescue_mode_enabled():
            for cmd in task.rescue_exec:
                subprocess.Popen([cmd])

    elif verify_result and not task.last_check_good and task.notify.get("on-rescued"):
        mailmanager.send_notify_mail(task)
