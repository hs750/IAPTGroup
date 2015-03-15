from IAPTlib import getTranscribeReviewForm
def view():
    projID = request.vars.get('id')
    project = db(db.projects.id == projID).select()[0]
    projectDocs = db(db.documents.projectID == projID).select()
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

    (numDocs, nextDocID, prevDocID, currentDocIndex) = getNextAndPrevious(docsInProj, document.id)

    # Generate the form
    form = getTranscribeReviewForm(True, requirements, False)
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

        # Close the project if all documents have been completed
        totalDocs = db(db.documents.projectID == document.projectID).count();
        completedDocs = db((db.documents.projectID == document.projectID) &
                           (db.documents.state == documentStates[1])).count()
        if totalDocs == completedDocs:
            proj = db(db.projects.id == document.projectID).select()[0]
            proj.state = projectStates[1]
            proj.update_record()

        response.flash = 'Transcription successfully saved.'
    contributed = not db((db.contributions.documentID == document.id) &
                         (db.contributions.userID == auth.user.id)).isempty()
    owningProject = db(db.projects.id == document.projectID).select(db.projects.id, db.projects.title)[0]

    return dict(form=form, doc=document, nextDocID=nextDocID, prevDocID=prevDocID, totalDocs=numDocs,
                currentDoc=currentDocIndex+1, contributed=contributed, owningProject=owningProject)

@auth.requires_login()
def review():
    response.subtitle = 'Review Project'
    projID = request.vars.get('id')
    documents = db(db.documents.projectID == projID).select()

    return dict(docs=documents)


@auth.requires_login()
def reviewDoc():
    response.subtitle = 'Review Document'
    docID = request.vars.get('id')

    document = db(db.documents.id == docID).select()[0]
    owningProject = db(db.projects.id == document.projectID).select(db.projects.id, db.projects.title)[0]

    usersTranscribed = db(db.contributions.documentID == docID).select(db.contributions.userID, distinct=True)
    for user in usersTranscribed:
        user.transcriptions = db((db.contributions.documentID == docID) &
                                 (db.contributions.userID == user.userID) &
                                 (db.contributions.requirementID == db.requirements.id)).select(
            db.requirements.type.with_alias('type'), db.requirements.name.with_alias('name'),
            db.contributions.content.with_alias('content'), db.contributions.id.with_alias('contribID')
        )

    docsInProj = db(db.documents.projectID == document.projectID).select(db.documents.id)
    (numDocs, nextDocID, prevDocID, currentDocIndex) = getNextAndPrevious(docsInProj, document.id)

    if request.vars.accepted is not None:
        accept = request.vars.accepted
        if accept == 'reject':
            for transcription in usersTranscribed:
                for trans in transcription.transcriptions:
                    contrib = db(db.contributions.id == trans.contribID).select()[0]
                    contrib.state = contributionStates[2]
                    contrib.update_record()
            document.state = documentStates[0]
            document.update_record()
        else:
            count = 1
            for transcription in usersTranscribed:
                if accept == str(count):
                    for trans in transcription.transcriptions:
                        contrib = db(db.contributions.id == trans.contribID).select()[0]
                        contrib.state = contributionStates[1]
                        contrib.update_record()
                else:
                    for trans in transcription.transcriptions:
                        contrib = db(db.contributions.id == trans.contribID).select()[0]
                        contrib.state = contributionStates[2]
                        contrib.update_record()
                count += 1
            document.state = documentStates[2]
            document.update_record()

    transcriptionStates = db(db.contributions.documentID == docID).select(db.contributions.userID,
                                                                          db.contributions.state, distinct=True)

    print transcriptionStates
    acceptedTrans = -1
    anyRejected = False
    for tState in transcriptionStates:
        if tState.state == contributionStates[1]:
            acceptedTrans = tState.userID
        elif tState.state == contributionStates[2]:
            anyRejected = True
    print acceptedTrans
    # -1 indicates nothing has been accepted or rejected, 0 indicates all rejected
    acceptedIndex = 0 if anyRejected else -1
    count = 1
    for user in usersTranscribed:
        if user.userID == acceptedTrans:
            acceptedIndex = count
        count += 1


    return dict(document=document, userTranscriptions=usersTranscribed, owningProject=owningProject,
                nextDocID=nextDocID, prevDocID=prevDocID, totalDocs=numDocs, currentDoc=currentDocIndex+1,
                acceptedTranscription=acceptedIndex)

def getNextAndPrevious(docsInProj, currentDocumentID):
    """
    Find the ids of the next and the previous documents
    :param docsInProj: a list of the documents in the project
    :param currentDocumentID: the id of the current document
    :return: number of documents, next document id, previous document id and the index in the list of the current document.
    """
    currentDocIndex = 0
    i = 0
    for doc in docsInProj:
        if doc.id == currentDocumentID:
            currentDocIndex = i
        i += 1

    numDocs = len(docsInProj)
    nextDocID = docsInProj[(currentDocIndex + 1) % numDocs].id
    prevDocID = docsInProj[(currentDocIndex - 1) % numDocs].id
    return (numDocs, nextDocID, prevDocID, currentDocIndex)