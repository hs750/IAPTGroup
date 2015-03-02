# -*- coding: utf-8 -*-

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
    if regform.accepts(request,session):
        #save user details to auth_user table. Encrypt password so that web2py's auth class can be used for login.
        db.auth_user.insert(first_name=request.vars.first_name,last_name=request.vars.surname, email=request.vars.email_address,password=db.auth_user.password.validate(request.vars.password)[0],username=request.vars.username)

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
            redirect(URL('default', 'index'))

    #if validation doesn't pass, highlight errors
    elif loginform.errors:
        response.flash = 'Login attempt failed. See below for more details.'
    return dict(form=loginform)
