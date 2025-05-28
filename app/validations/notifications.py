def createNotificationValidations(user_ids, event_id, title, message, priority):

    errors = {}
    validations_pass = True

    title = title.strip()
    if title == "":
        errors["title"] = "Por favor ingrese un titulo"

    titleMaxLen = 50
    if len(title) > titleMaxLen:
        errors["title"] = "Maximo " + str(titleMaxLen) + " caracteres"

    message = message.strip()
    if message == "":
        errors["message"] = "Por favor ingrese un mensaje"

    messageMaxLen = 100
    if len(message) > messageMaxLen:
        errors["message"] = "Maximo " + str(messageMaxLen) + " caracteres"

    if priority == "":
        errors["priority"] = "Por favor seleccione una prioridad"
    else:
        optionList = ["LOW", "MEDIUM", "HIGH"]
        if priority not in optionList:
            errors["priority"] = "La prioridad debe ser Baja, Media o Alta"

    if len(user_ids) == 0:
        errors["user"] = "Por favor seleccione un usuario"
    
    if not event_id:
        errors["event"] = "Por favor seleccione un evento"
    
    if len(errors.keys()) > 0:
        validations_pass = False

    return validations_pass, errors