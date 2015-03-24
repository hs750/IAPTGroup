# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################
from operator import itemgetter
from IAPTlib import addImagesToProjects
from IAPTlib import searchProjects

def index():

    # The newest 5 projects
    newest = db((db.projects.id > 0) &
                (db.projects.state == projectStates[0])).select(orderby=~db.projects.id, limitby=(0, 5))

    # The most popular projects
    # 'Popular' means projests which have the highest ratio of documents completed.
    allDocs = db(db.documents.id > 0 ).select()
    projectDocs = dict()
    projectCompletedDocs = dict()

    for doc in allDocs:
        projID = doc.projectID
        docsForProj = projectDocs.get(projID, 0)
        projectDocs[projID] = docsForProj + 1
        if doc.state == documentStates[1]:
            compDocForProj = projectCompletedDocs.get(projID, 0)
            projectCompletedDocs[projID] = compDocForProj + 1

    projPercentateComplete = dict()

    for projID in projectDocs.keys():
        projCompleted = float(projectCompletedDocs.get(projID, 0)) / float(projectDocs.get(projID))
        projPercentateComplete[projID] = projCompleted

    projPercentateComplete = projPercentateComplete.items()

    # Projects ordered by popularity, highest first
    projPercentateComplete = sorted(projPercentateComplete, key=itemgetter(1), reverse=True)

    # Top 5 must popular projects
    projPercentateComplete = projPercentateComplete[0:5]

    topFiveIDs = []
    for i in range(0,min(5, len(projPercentateComplete))):
        topFiveIDs.append(projPercentateComplete[i][0])

    topFive = db(db.projects.id.belongs(topFiveIDs) & (db.projects.state == projectStates[0])).select()

    newest = addImagesToProjects(newest, db)
    topFive = addImagesToProjects(topFive, db)

    return dict(new=newest, topFive=topFive)

@auth.requires_login()
def create():
    # Clean temporary variables
    session.tempVars = {}
    db(db.tempUpload.sessionID == response.session_id).delete()
    return dict()

# Part One contains title, description, keywords
def createPartOne():
    # Create form
    form = FORM(DIV(LABEL('Title:', _for='title', _class="create-form-label"),
        INPUT(_name='title', _id='title', _class="create-form-field",requires=IS_NOT_EMPTY()),
        BR(), I('A short title for your project', _class="create-form-alttext"), _class="create-form-item"),
    DIV(LABEL('Description:', _for='description', _class="create-form-label"),
        TEXTAREA(_name='description', _id='description', _rows = 3, _style ='width:300px;', _class="create-form-field",requires=IS_NOT_EMPTY()),
        BR(), I('You can make the description as detailed as you like. It\'s purpose is to give people an introduction to the project.', _class="create-form-alttext"), _class="create-form-item"),
    DIV(LABEL('Keywords:', _for='keywords', _class="create-form-label"),
        INPUT(_name='keywords', _id='keywords', _class="create-form-field"),
        BR(), I('Descriptive keywords will make it easier for people to find your project when searching. Separate keywords by using commas or spaces.', _class="create-form-alttext"), _class="create-form-item"))


    nextButton = [TAG.button('Next',_type="submit")]
    form.append(DIV(nextButton))

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
    form = FORM(DIV(LABEL('Requirements:', _for='basereq', _class="create-form-label"),
        INPUT(_name='basereq', _id='basereq', _class='create-form-field', requires=IS_NOT_EMPTY()),
        INPUT(_value='+', _type='button', _class='create-req-btn', _onClick='addReq($("#basereq").val());'),
        BR(), DIV(_id='wrapper', _class='create-req-wrapper')), _id='reqForm')
    
    # Add form nav buttons
    nextPrevButtons = [TAG.button('Back', _type="button",_onClick = "jQuery('.createDivTwo').hide(); jQuery('.createDivOne').show(); $('#keywords').tagit();"),TAG.button('Next',_type="submit")]
    form.append(DIV(nextPrevButtons))

    if form.validate(keepvalues=True):
        # Add base requirement to the others for submission.
        reqs = [form.vars.basereq]
        if 'requirements' in session.tempVars:
            for r in session.tempVars['requirements']:
                reqs.append(r)
        session.tempVars['requirements'] = reqs

        # Go to next part of form
        response.js = "jQuery('.createDivTwo').hide(); jQuery('.createDivThree').show();"
    return dict(form=form)

# Part Three contains image upload, though they are displayed in a seperate component.
def createPartThree():
    # Create upload form
    form = FORM(DIV(LABEL('Add Files:', _for='upload', _class="create-form-label"),
        INPUT(_name='uploadFiles', _id='uploadField', _type='file', _multiple='',_class='upload create-form-field'),
        BR()), _id='uploadForm')

    # Upload button
    uploadButton = TAG.button('Upload',_type="submit")
    form.append(uploadButton)

    # If files are uploaded
    if form.accepts(request.vars):
        # Get files
        files = request.vars['uploadFiles']
        # If singular file and not multiple, make into list
        if not isinstance(files, list):
            files = [files]
        # For each file uploaded:
        for f in files:
            uploadedFile = db.tempUpload.image.store(f, f.filename)
            i = db.tempUpload.insert(image=uploadedFile, sessionID=response.session_id)
            db.commit()
        # Reload component to show uploaded files and edit info
        response.js = "jQuery('#documentsDisplay').get(0).reload();"
    return dict(form=form)

# displayDocuments allows users to give info about doc images they just uploaded.
# Its submit button creates the project.
def displayDocuments():
    # Get documents that have been uploaded
    documents = db(db.tempUpload.sessionID == response.session_id).select()

    divWrapper = DIV(_class='create-form-doc-wrapper')
    # Construct divs for each document
    for index, doc in enumerate(documents):
        # Get image and filename
        (filename, stream) = db.tempUpload.image.retrieve(doc.image)
        # For each document, we need to construct a form for setting title and description.
        # Unique ids are also required so we use the index of the loop.
        docImg = IMG(_src=URL('default', 'getImage', args=[doc.image]), _id='docimg%s' % index, _class='create-form-doc-img')
        docTitle = DIV(LABEL('Title:', _for='doctitle%s' % index, _class="create-form-label"),
            INPUT(_name='title%s' % index, _value=filename,_id='doctitle%s' % index, _class="create-form-field", requires=IS_NOT_EMPTY()),
            _class='create-form-doc-title')
        docDesc = DIV(LABEL('Description:', _for='docdesc%s' % index, _class="create-form-label"),
            TEXTAREA(_name='desc%s' % index, _id='docdesc%s' % index, _rows = 3, _style ='width:300px;', _class="create-form-field", requires=IS_NOT_EMPTY()),
            _class='create-form-doc-desc')
        docItem = DIV(docImg, docTitle, docDesc, _id='docitem%s' % index,_class='create-form-doc-item')
        # Append item to the wrapper div
        divWrapper.append(docItem)

    # Construct the form containing all doc items.
    form = FORM(divWrapper)
    # Add form nav buttons
    nextPrevButtons = [TAG.button('Back', _type="button",_onClick = "jQuery('.createDivThree').hide(); jQuery('.createDivTwo').show()"),TAG.button('Submit',_type="submit")]
    form.append(DIV(nextPrevButtons))

    # If form accepts, process all data
    if form.accepts(request.vars):
        # Create project
        newProj = db.projects.insert(title=session.tempVars['title'], description=session.tempVars['desc'], state='open',userID=auth.user)

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
            db.requirements.insert(name=r, type='Short Text', projectID=newProj.id)

        # Add documents
        for index, doc in enumerate(documents):
            # Fetch values from form
            docTitle = request.vars['title%s' % index]
            docDesc = request.vars['desc%s' % index]
            db.documents.insert(title=docTitle,description=docDesc,image=doc.image,state='open',projectID=newProj.id)

        # Creation is done, return to home page?
        redirect(URL('default', 'index', extension='html'), client_side=True)

    return dict(form=form)

# Web2py doesnt seem to have any way of accessing form input variables that werent present during creation
# So this keeps a sepearate list to refer to.
def updateReqs():
    session.tempVars['requirements'] = request.vars.values()[0]
    return dict()

def liveSearch():
    searchStr = request.vars.values()[0]
    projects = searchProjects(searchStr, db)
    addImagesToProjects(projects, db)
    items = []
    for (i, project) in enumerate(projects):
        nameDiv = H4(project.title, _class="liveSearchResultTileTitle", _id="res%s"%i)
        imgDiv = DIV(IMG(_src=URL('default', 'getImage', args=[project.image]), _alt=project.imageAlt), _class="liveSearchResultTileImg")
        descDiv = DIV(project.description, _class="liveSearchResultTileDesc")
        items.append(A(nameDiv, imgDiv, descDiv, _href="#", _onclick="copyIntoSearch($('#res%s').html())"%i, _class="liveSearchResult"))
    return TAG[''](*items)

def dashboard():
    return index()

def browse():
    if request.vars.search is None:
        searchTerms = ''
    else:
        searchTerms = request.vars.search

    results = searchProjects(searchTerms, db)
    searchForm = FORM(INPUT(_type='search', _placeholder='Search', _name='searchField'),
                      INPUT(_type='submit', _value='Search', _name='searchSubmit'),
                      _name='searchForm',
                      _class='form-inline',
                      _id='searchForm')

    if searchForm.accepts(request.post_vars):
        redirect(URL(vars=dict(search=request.post_vars.searchField)))

    results = addImagesToProjects(results, db)
    return dict(form=searchForm, projects=results)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)

def getImage():
    """
    Get an image. Which image to get is stored in request.
    This method should only be called as part of a URL for displaying images on the page
    :return: the  image
    """
    return response.download(request, db)
