
def view():
    projID = request.vars.get('id')
    project = db(db.projects.id == projID).select()[0]
    projectDocs = db((db.documents.projectID == projID) & (db.documents.state == documentStates[0])).select()
    owner = db(db.auth_user.id == project.userID).select(db.auth_user.username)[0]
    return dict(project=project, docs=projectDocs, owner=owner)


def transcribe():
    docID = request.vars.get('id')
    return dict()