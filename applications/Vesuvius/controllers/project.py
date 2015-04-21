from IAPTlib import getTranscribeReviewForm
def view():
    response.subtitle = 'View Project'
    projID = request.vars.get('id')
    project = db(db.projects.id == projID).select()[0]
    projectDocs = db((db.documents.projectID == projID) & (db.documents.state != documentStates[2])).select()
    owner = db(db.auth_user.id == project.userID).select(db.auth_user.username)[0]
    return dict(project=project, docs=projectDocs, owner=owner)

@auth.requires_login()
def transcribe():
    response.subtitle = 'Transcribe Document'
    docID = request.vars.get('id')

    # The current document and the requirements needed for it
    document = db((db.documents.id == docID) & (db.documents.state == documentStates[0])).select()[0]
    requirements = db(db.requirements.projectID == document.projectID).select()

    # Work out the IDs of the next and the previous documents from the current on.
    docsInProj = db((db.documents.projectID == document.projectID)
                    & (db.documents.state == documentStates[0])).select(db.documents.id)

    (numDocs, nextDocID, prevDocID, currentDocIndex) = getNextAndPrevious(docsInProj, document.id)

    # Generate the form
    (form, rCount) = getTranscribeReviewForm(True, requirements, False)
    form.append(DIV(DIV(INPUT(_value='Submit Transcription', _name='submit', _type='submit', _class='btn btn-primary'), _class='controls'), _class='control-group'))

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

        # If the number of pending contributions to the document is greater than 3, close the document
        numContibs = db((db.contributions.documentID == docID) &
                        (db.contributions.requirementID == requirements[0].id) &
                        (db.contributions.state == contributionStates[0])).count()
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

    # Has anyone contributed to this document
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

    # Collate the transcriptions made my each user to the document
    usersTranscribed = db(db.contributions.documentID == docID).select(db.contributions.userID, distinct=True)
    for user in usersTranscribed:
        user.transcriptions = db((db.contributions.documentID == docID) &
                                 (db.contributions.userID == user.userID) &
                                 (db.contributions.requirementID == db.requirements.id)).select(
            db.requirements.name.with_alias('name'),
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

    # Work out which transcription has been accepted (if any (non = -1))
    acceptedTrans = -1
    anyRejected = False
    for tState in transcriptionStates:
        if tState.state == contributionStates[1]:
            acceptedTrans = tState.userID
        elif tState.state == contributionStates[2]:
            anyRejected = True

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

@auth.requires_login()
def create():
    response.subtitle = 'Create Project'
    # Clean temporary variables
    session.tempVars = {}
    db(db.tempUpload.sessionID == response.session_id).delete()
    return dict()

# Part One contains title, description, keywords
def createPartOne():
    # Create form
    form = FORM(DIV(LABEL('Title: *', _for='title', _class="create-form-label"),
        INPUT(_name='title', _id='title', _class="create-form-field",requires=IS_NOT_EMPTY(error_message='A Project must have a Title')),
         I('A short title for your project', _class="create-form-alttext"), _class="create-form-item"),
    DIV(LABEL('Description:', _for='description', _class="create-form-label"),
        TEXTAREA(_name='description', _id='description', _rows = 3, _style ='width:300px;', _class="create-form-field"),
         I('You can make the description as detailed as you like. It\'s purpose is to give people an introduction to the project.', _class="create-form-alttext"), _class="create-form-item"),
    DIV(LABEL('Keywords:', _for='keywords', _class="create-form-label"),
        INPUT(_name='keywords', _id='keywords', _class="create-form-field"),
         I('Descriptive keywords will make it easier for people to find your project when searching. Separate keywords by using commas or spaces.', _class="create-form-alttext"),_class="create-form-item"),
        DIV('* indicates required field.', _class="create-form-alttext"),BR(), _class="create-req-form")


    nextButton = [TAG.button('Next',_type="submit")]
    form.append(DIV(nextButton, _class="create-form-btn-right"))

    # Turn keywords input into a tagit field.
    response.js = "$('#keywords').tagit();"

    # If Next clicked and validated and open second part of form
    if form.validate(keepvalues=True):
        # Save vars in session
        session.tempVars['title'] = form.vars.title
        session.tempVars['desc'] = form.vars.description
        session.tempVars['keywords'] = form.vars.keywords

        # Go to next part of form
        response.js = "jQuery('.createDivOne').hide(); jQuery('.createDivTwo').show();"
    return dict(form=form)

# Part Two contains requirements
def createPartTwo():
    # Create requirements form
    form = FORM(DIV(LABEL('Requirements: *', _for='basereq', _class="create-form-label"),
        INPUT(_name='basereq', _id='basereq', _class='create-req-field'),
        INPUT(_value='+', _type='button', _class='create-req-btn', _onClick='addReq($("#basereq").val());errorClear($("#basereq").parent());clearField(basereq);$("#basereq").focus();'),
        BR(), DIV(_id='wrapper', _class='create-req-wrapper'), _class="create-req-item"), BR(), _class="create-req-form", _id='reqForm')

    # Get requirements already entered
    query = ''
    if 'requirements' in session.tempVars:
        curReqs = session.tempVars['requirements']
        if isinstance(curReqs, basestring):
            curReqs = [curReqs]
        for req in curReqs:
            query = query +'addReq("%s");' % req
    response.js = query

    # Add form nav buttons
    nextPrevButtons = [TAG.button('Back', _type="button",_onClick = "jQuery('.createDivTwo').hide(); jQuery('.createDivOne').show(); $('#keywords').tagit();"),TAG.button('Next',_type="submit")]
    form.append(DIV(nextPrevButtons, _class="create-form-btn-right"))

    if form.validate(keepvalues=True):
        if form.vars.basereq or (('requirements' in session.tempVars) and session.tempVars['requirements'] != []):
            # Add base requirement to the others for submission.
            reqs = []
            if form.vars.basereq:
                reqs.append(form.vars.basereq)
            if 'requirements' in session.tempVars:
                for r in session.tempVars['requirements']:
                    reqs.append(r)
            # Save requirements in session variable
            session.tempVars['requirements'] = reqs

            # Go to next part of form
            response.js = "jQuery('.createDivTwo').hide(); jQuery('.createDivThree').show();"
        else:
            response.js = "errorMove($('#basereq').parent());"
            form.errors.basereq ='Please enter a requirement.'

    return dict(form=form)

# Part Three contains image upload, though they are displayed in a seperate component.
def createPartThree():
    # Create upload form
    form = FORM(DIV(LABEL('Add Files: *', _for='upload', _class="create-form-label"),
        INPUT(_name='uploadFiles', _id='uploadField', _type='file', _multiple='', _class='upload create-form-field'),
        DIV(TAG.button('Upload',_type="submit", _id='submitUpload'), _style='display:inline-block;'),
        BR()), _class="create-upl-form", _id='uploadForm')

    # Upload button
    #uploadButton = TAG.button('Upload',_type="submit", _id='submitUpload')
    #form.append(uploadButton)

    # If files are uploaded
    if form.accepts(request.vars):
        # Get files
        files = request.vars['uploadFiles']
        if files == '':
            # Reset button if no files were added.
            response.js = "jQuery('#submitUpload').addClass('btn');errorMove($('#uploadField').parent());"
            form.errors.uploadFiles = 'You did not select any files to upload!'
        else:
            # If singular file and not multiple, make into list
            if not isinstance(files, list):
                files = [files]

            errorFiles = []
            # For each file uploaded:
            for f in files:
                # Check file type
                if (f.filename.split(".")[-1].lower() in ['jpeg', 'png', 'jpg', 'gif', 'bmp']):
                    uploadedFile = db.tempUpload.image.store(f, f.filename)
                    i = db.tempUpload.insert(image=uploadedFile, sessionID=response.session_id)
                    db.commit()
                else:
                    # Not a supported image.
                    errorFiles += [f.filename]
            if len(errorFiles) > 0:
                errorMessage = ''
                if len(errorFiles) == 1:
                    errorMessage = errorFiles[0] + ' is not a supported image type.'
                else:
                    errorMessage = str(errorFiles) + ' are not supported image types.'
                errorMessage += ' Please select jpeg, png, jpg, gif or bmp image files.'
                form.errors.uploadFiles = errorMessage
            # Reload component to show uploaded files and edit info, also reset button style.
            response.js = "jQuery('#submitUpload').addClass('btn'); jQuery('#documentsDisplay').get(0).reload();"
    return dict(form=form)

# displayDocuments allows users to give info about doc images they just uploaded.
# Its submit button creates the project.
def displayDocuments():
    # Get documents that have been uploaded
    documents = db(db.tempUpload.sessionID == response.session_id).select()

    divWrapper = DIV(_class='create-form-doc-wrapper', _id='createdocwrapper')
    # Construct divs for each document
    for index, doc in enumerate(documents):
        # Get image and filename
        (filename, stream) = db.tempUpload.image.retrieve(doc.image)
        # For each document, we need to construct a form for setting title and description.
        # Unique ids are also required so we use the index of the loop.
        docImg = IMG(_src=URL('default', 'getImage', args=[doc.image]), _id='docimg%s' % index, _class='create-form-doc-img')
        docTitle = DIV(LABEL('Title:', _for='doctitle%s' % index, _class="create-form-label"),
            INPUT(_name='title%s' % index, _value=filename,_id='doctitle%s' % index, _class="create-form-field", requires=IS_NOT_EMPTY(error_message='Enter a Title for the Document')),
            _class='create-form-doc-title')
        docDesc = DIV(LABEL('Description:', _for='docdesc%s' % index, _class="create-form-label"),
            TEXTAREA(_name='desc%s' % index, _id='docdesc%s' % index, _rows = 3, _style ='width:300px;', _class="create-form-field", requires=IS_NOT_EMPTY(error_message='Enter a Description of the Document')),
            _class='create-form-doc-desc')
        docItem = DIV(docImg, docTitle, docDesc, _id='docitem%s' % index,_class='create-form-doc-item')
        # Append item to the wrapper div
        divWrapper.append(docItem)

    # Construct the form containing all doc items.
    form = FORM(divWrapper, BR(), _class="create-upl-form")
    # Add form nav buttons
    nextPrevButtons = [TAG.button('Back', _type="button",_onClick = "jQuery('#partTwoForm').get(0).reload();jQuery('.createDivThree').hide(); jQuery('.createDivTwo').show()")]
    if documents:
        nextPrevButtons += [TAG.button('Submit',_type="submit")]
    else:
        nextPrevButtons += [TAG.button('Submit',_type="submit", _disabled="true")]
    form.append(DIV(nextPrevButtons, _class="create-form-btn-right"))

    # If form accepts, process all data
    if form.accepts(request.vars):
        # Create project
        newProj = db.projects.insert(title=session.tempVars['title'], description=session.tempVars['desc'], state='closed',userID=auth.user)

        # Add project keywords
        keywords = session.tempVars['keywords'].split(',')
        for k in keywords:
            if db(db.keywords.keyword == k).isempty():
                key = db.keywords.insert(keyword=k)
            else:
                key = db(db.keywords.keyword == k).select().first()
            db.projectKeywords.insert(keywordID=key.id, projectID=newProj.id)

        # Add requirements
        requirements = session.tempVars['requirements']
        for r in requirements:
            db.requirements.insert(name=r, projectID=newProj.id)

        # Add documents
        for index, doc in enumerate(documents):
            # Fetch values from form
            docTitle = request.vars['title%s' % index]
            docDesc = request.vars['desc%s' % index]
            db.documents.insert(title=docTitle,description=docDesc,image=doc.image,state='open',projectID=newProj.id)

        # Creation is done, open dashboard
        redirect(URL('user', 'dashboard', extension='html', vars=dict(created=session.tempVars['title'])), client_side=True)

    return dict(form=form)

# Web2py doesnt seem to have any way of accessing form input variables that werent present during creation
# So this keeps a sepearate list to refer to.
def updateReqs():
    # Get requirements from request
    reqList = request.vars.values()[0]
    # Ensure it is a list, and not a normal string.
    if isinstance(reqList, basestring):
        reqList = [reqList]
    # Store in tempVars
    if(reqList[0] != ""):
        session.tempVars['requirements'] = reqList
    else:
        session.tempVars['requirements'] = []
    return dict()