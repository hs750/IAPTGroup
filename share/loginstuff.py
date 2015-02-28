
### userOnly and validateUser are defined in a model file and can be called from any controller.
### validateUser is called at the top of every controller to update the currentUser variable if the user is logged in, or sets it to null if not.
### userOnly is called at the top of the page functions for every page that needs the user to be logged in first.

# Check if a user is logged in, and set to request.currentUser
def validateUser(request):
    request.currentUser = ''
    if request.cookies.has_key('logincookie'):
        activeCookie = request.cookies['logincookie'].value
        if (len(activeCookie) >0) :
            userSession = db(db.UserSessions.cookie_id==activeCookie).select().first()
            if userSession:
                request.currentUser = db.Users[userSession.user_id]

# Call in pages that require an active user to redirect to login page
# Also serves to redirect to index if user must not be logged in to access page
def userOnly(userOnly = True):
    if userOnly:
        if not request.currentUser:
            redirect(URL('login'))
    else:
        if request.currentUser:
            redirect(URL('index'))


### With this user variable current_user, we can implement a modified version of the web2py context-sensitive login/register navbar section

def navbar(current_user):
    if not current_user:
        btn_login = A(current.T("Login"),
                    _href=URL('default','login'),
                    _class="btn btn-success",
                    _rel="nofollow")
        btn_register = A(current.T("Sign Up"),
                    _href=URL('register','register'),
                    _class="btn btn-success",
                    _rel="nofollow")
        return DIV(btn_register, btn_login, _class="btn-group")
    else:
        welcome = "Welcome %s!" % current_user.firstname.capitalize()
        toggle = A(welcome, _href="#", _class="dropdown-toggle",
                _rel="nofollow", **{"_data-toggle": "dropdown"})

        li_profile = LI(A(I(_class="icon-user"), ' ',
                          current.T("My User Page"),
                          _href=URL('default','user'), _rel="nofollow"))
        li_custom = LI(A(I(_class="icon-book"), ' ',
                         current.T("My Bootables"),
                         _href=URL('default','manager'), rel="nofollow"))
        li_logout = LI(A(I(_class="icon-off"), ' ',
                         current.T("Logout"),
                         _href=URL('default','logout'), _rel="nofollow"))
        dropdown = UL(li_profile,
                      li_custom,
                      LI('', _class="divider"),
                      li_logout,
                      _class="dropdown-menu", _role="menu")

        return LI(toggle, dropdown, _class="dropdown")