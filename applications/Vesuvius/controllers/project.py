
def view():
    projID = request.vars.get('id')
    project = db(db.projects.id == projID).select()[0]
    projectDocs = db((db.documents.projectID == projID) & (db.documents.state == documentStates[0])).select()
    owner = db(db.auth_user.id == project.userID).select(db.auth_user.username)[0]
    return dict(project=project, docs=projectDocs, owner=owner)

@auth.requires_login()
def transcribe():
    response.subtitle = 'Transcribe'
    docID = request.vars.get('id')

    # The current document and the requirements needed for it
    document = db((db.documents.id == docID) & (db.documents.state == documentStates[0])).select()[0]
    requirements = db(db.requirements.projectID == document.projectID).select()

    # Work out the IDs of the next and the previous documents from the current on.
    docsInProj = db((db.documents.projectID == document.projectID)
                    & (db.documents.state == documentStates[0])).select(db.documents.id)

    currentDocIndex = 0
    i = 0
    for doc in docsInProj:
        if doc.id == document.id:
            currentDocIndex = i
        i += 1

    numDocs = len(docsInProj)
    nextDocID = docsInProj[(currentDocIndex + 1) % numDocs].id
    prevDocID = docsInProj[(currentDocIndex - 1) % numDocs].id

    # Generate the form
    form = FORM(_class='form-horizontal')

    rCount = 0
    for req in requirements:
        intputName = 'req-' + str(rCount)
        ctrlGroup = DIV(_class='control-group')
        ctrlGroup.append(LABEL(req.name, _for=intputName, _class='control-label'))
        input = INPUT(_name=intputName)
        if req.type == requirementTypes[0]:
            input = INPUT(_name=intputName)
        elif req.type == requirementTypes[1]:
            input = TEXTAREA(_name=intputName)
        elif req.type == requirementTypes[2]:
            input = INPUT(_name=intputName, _type='date')
        elif req.type == requirementTypes[3]:
            input = INPUT(_name=intputName, _type='number')

        ctrlGroup.append(DIV(input, _class='controls'))
        form.append(ctrlGroup)
        rCount += 1
    form.append(DIV(DIV(INPUT(_name='submit', _type='submit'), _class='controls'), _class='control-group'))

    if form.accepts(request.post_vars):
        # Insert each requirement transcription into the database
        for i in range(0, rCount):
            req = requirements[i]
            reqInput = 'req-' + str(i)

            # Insert into database even if the field is empty. This is not the most efficient storage method,
            # however it makes checking the number of contributions easy
            db.contributions.insert(
                content=request.post_vars[reqInput],
                state=contributionStates[0],
                userID=auth.user.id,
                documentID=docID,
                requirementID=req.id
            )

        # If the number of contributions to the document is greater than 3, close the document
        numContibs = db((db.contributions.documentID == docID) & (db.contributions.requirementID == requirements[0].id)).count()
        if numContibs >= 3:
            document.state = documentStates[1]
            document.update_record()

        redirect(URL('view', vars=dict(id=document.projectID)))
        response.flash = 'Transcription successfully saved.'

    return dict(form=form, doc=document, nextDocID=nextDocID, prevDocID=prevDocID, totalDocs=numDocs,
                currentDoc=currentDocIndex+1)