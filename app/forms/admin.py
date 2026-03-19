from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField, StringField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email
from app.models.enums import TicketStatus

class UpdateTicketStatusForm(FlaskForm):
    # Usamos s.value para el valor enviado y s.label para el texto mostrado
    status = SelectField('Estado', choices=[(s.value, s.label) for s in TicketStatus], validators=[DataRequired(message="Campo obligatorio")])
    note = TextAreaField('Nota Interna', validators=[Length(max=500, message="Máximo 500 caracteres")])
    submit = SubmitField('Actualizar Ticket')

class ContactForm(FlaskForm):
    name = StringField('Nombre de la Dirección / Municipio', validators=[DataRequired(message="Campo obligatorio"), Length(max=100)])
    email = StringField('Correo Electrónico', validators=[DataRequired(message="Campo obligatorio"), Email(message="Email inválido")])
    submit = SubmitField('Guardar en Agenda')

class SendEmailForm(FlaskForm):
    contact_id = SelectField('Destinatario (Agenda)', coerce=int, validators=[DataRequired(message="Debe seleccionar un destinatario")])
    ticket_ids = SelectMultipleField('Tickets Relacionados (Pendientes)', coerce=str)
    subject = StringField('Asunto', validators=[DataRequired(message="Campo obligatorio"), Length(max=255)])
    message = TextAreaField('Mensaje / Cuerpo del Correo', validators=[DataRequired(message="Campo obligatorio")])
    submit = SubmitField('Enviar Correo')
