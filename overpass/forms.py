from wtforms import Form, StringField, TextAreaField, BooleanField, validators


class StreamGenerationForm(Form):
    title = StringField("Title", [validators.DataRequired()])
    description = TextAreaField("Description", [validators.DataRequired()])
    category = StringField("Category")
    archivable = BooleanField("Archive the stream")
    unlisted = BooleanField("Unlisted")
