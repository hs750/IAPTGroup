# -*- coding: utf-8 -*-

def create():
    #define the registration form structure with all fields and validation
    regform = FORM(DIV(LABEL('Username', _for='username',_class="control-label"),
                       DIV(INPUT(_name='username',requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'auth_user.username',error_message='An account already exists with this username.')]),_class="controls"),_class="control-group"),
                   DIV(LABEL('E-mail address', _for='email_address',_class="control-label"),
                       DIV(INPUT(_name='email_address',requires=[IS_NOT_EMPTY(), IS_EMAIL(),IS_NOT_IN_DB(db,'auth_user.email',error_message='An account already exists with this e-mail address')], _placeholder='yourname@example.com'),_class="controls"),_class="control-group"),
                   DIV(LABEL('First name', _for='first_name',_class="control-label"),
                       DIV(INPUT(_name='first_name', requires=IS_NOT_EMPTY()),_class="controls"),_class="control-group"),
                   DIV(LABEL('Surname', _for='surname',_class="control-label"),
                       DIV(INPUT(_name='surname',requires=IS_NOT_EMPTY()),_class="controls"),_class="control-group"),
                   DIV(LABEL('Password', _for='password',_class="control-label"),
                       DIV(INPUT(_name='password', _type='password',requires=IS_NOT_EMPTY()),_class="controls"),_class="control-group"),
                   DIV(LABEL('Confirm password', _for='confirm_password',_class="control-label"),
                       DIV(INPUT(_name='confirm_password', _type='password',requires=[IS_NOT_EMPTY(),IS_EQUAL_TO(request.vars.password,error_message='Password fields do not match')]),_class="controls"),_class="control-group"),
                   DIV(DIV(INPUT(_type='submit',_id='user-reg-button', _value='Create',_class='btn btn-primary'),_class='controls'),_class='control-group'),_class="form-horizontal")

    #if form is submitted and validation passes
    if regform.accepts(request,session):
        #save user details to auth_user table. Encrypt password so that web2py's auth class can be used for login.
        db.auth_user.insert(first_name=request.vars.first_name,last_name=request.vars.surname, email=request.vars.email_address,password=db.auth_user.password.validate(request.vars.password)[0],username=request.vars.username)

        db.commit
        redirect(URL('default','user/login'))

    #if validation doesn't pass, highlight errors
    elif regform.errors:
        response.flash = 'The registration form has errors. Please see below for more information.'
    return dict(form=regform)
