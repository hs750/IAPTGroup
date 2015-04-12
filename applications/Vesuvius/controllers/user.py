# -*- coding: utf-8 -*-
from IAPTlib import addImagesToProjects

def create():
    #define the registration form structure with all fields and validation
    #TODO: Customise error messages to make them more useful for the user (more specific than 'enter a value')
    regform = FORM(DIV(LABEL('Username', _for='username',_class="control-label"),
                       DIV(INPUT(_name='username',_id='username',requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'auth_user.username',error_message='An account already exists with this username.')]),_class="controls"),_class="control-group"),
                   DIV(LABEL('E-mail address', _for='email_address',_class="control-label"),
                       DIV(INPUT(_name='email_address',_id='email',requires=[IS_NOT_EMPTY(), IS_EMAIL(),IS_NOT_IN_DB(db,'auth_user.email',error_message='An account already exists with this e-mail address')], _placeholder='yourname@example.com'),_class="controls"),_class="control-group"),
                   DIV(LABEL('First name', _for='first_name',_class="control-label"),
                       DIV(INPUT(_name='first_name',_id='first_name', requires=IS_NOT_EMPTY()),_class="controls"),_class="control-group"),
                   DIV(LABEL('Surname', _for='surname',_class="control-label"),
                       DIV(INPUT(_name='surname',_id='surname',requires=IS_NOT_EMPTY()),_class="controls"),_class="control-group"),
                   DIV(LABEL('Password', _for='password',_class="control-label"),
                       DIV(INPUT(_name='password',_id='password', _type='password',requires=IS_NOT_EMPTY()),_class="controls"),_class="control-group"),
                   DIV(LABEL('Confirm password', _for='confirm_password',_class="control-label"),
                       DIV(INPUT(_name='confirm_password',_id='confirm_password', _type='password',requires=[IS_NOT_EMPTY(),IS_EQUAL_TO(request.vars.password,error_message='Password fields do not match')]),_class="controls"),_class="control-group"),
                   DIV(DIV(INPUT(_type='submit',_id='user-reg-button', _value='Create',_class='btn btn-primary'),_class='controls'),_class='control-group'),_class="form-horizontal")

    #if form is submitted and validation passes
    if regform.accepts(request,session, keepvalues=True):
        #save user details to auth_user table. Encrypt password so that web2py's auth class can be used for login.
        password = db.auth_user.password.validate(request.vars.password)
        if password[0] == '':
            regform.errors.password = password[1]
        else:
            db.auth_user.insert(first_name=request.vars.first_name,
                                last_name=request.vars.surname,
                                email=request.vars.email_address,
                                password=password[0],
                                username=request.vars.username)
            auth.login_bare(request.vars.username, request.vars.password)
            redirect(URL('default', 'index'))

    #if validation doesn't pass, highlight errors
    elif regform.errors:
        response.flash = 'The registration form has errors. Please see below for more information.'
    return dict(form=regform)

def login():
    #define the registration form structure with all fields and validation
    #TODO: Customise error messages to make them more useful for the user (more specific than 'enter a value')
    loginform = FORM(DIV(LABEL('Username', _for='username',_class="control-label"),
                       DIV(INPUT(_name='username',_id='username',requires=[IS_NOT_EMPTY()]),_class="controls"),_class="control-group"),
                   DIV(LABEL('Password', _for='password',_class="control-label"),
                       DIV(INPUT(_name='password',_id='password', _type='password',requires=IS_NOT_EMPTY()),_class="controls"),_class="control-group"),
                   DIV(DIV(INPUT(_type='submit',_id='login-button', _value='Sign In',_class='btn btn-primary'),_class='controls'),_class='control-group'),_class="form-horizontal")

    #if form is submitted and validation passes
    if loginform.accepts(request,session):
        #attempt login - if successful, redirect to home page
        if not auth.login_bare(request.vars.username, request.vars.password):
            #TODO: improve response message to include links to forgot username/password forms (below doesn't output link)
            #response.flash = 'Login attempt failed. Have you forgotten your <a href="' + URL('default','user',args=['retrieve_username']) + '">username</a> or password?'
            response.flash = 'Login attempt failed. Please try again'
        else:
            redirect(session.returnURL)
    #if validation doesn't pass, highlight errors
    elif loginform.errors:
        response.flash = 'Login attempt failed. See below for more details.'
    #Save URL for redirect
    else:
        session.returnURL = request.env.http_referer
    return dict(form=loginform)

@auth.requires_login()
def dashboard():
    if request.vars.action is not None and request.vars.id is not None:
        proj = db(db.projects.id == request.vars.id).select()[0]
        if request.vars.action == 'Open':
            proj.state = projectStates[0]
        elif request.vars.action == 'Close':
            proj.state = projectStates[1]
        proj.update_record()

    projects = db(db.projects.userID == auth.user.id).select()
    projects = addImagesToProjects(projects, db)

    transcriptions = db((db.contributions.userID == auth.user.id) &
                        (db.contributions.documentID == db.documents.id) &
                        (db.documents.projectID == db.projects.id)
                        ).select(db.contributions.content, db.contributions.state, db.projects.title, db.documents.title)

    for project in projects:
        docs = db(db.documents.projectID == project.id).count()
        completeDocs = db((db.documents.projectID == project.id) & (db.documents.state != documentStates[0])).count()
        project.totalDocs = docs
        project.compDocs = completeDocs

    return dict(projects=projects, transcriptions=transcriptions)
