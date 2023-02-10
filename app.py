#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config') # URI stored in config.py

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.app_context().push()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    website_link = db.Column(db.String(240))
    facebook_link = db.Column(db.String(240))
    genres = db.Column(db.String(120), nullable=False)
    seeking = db.Column(db.Boolean, default=False)
    seeking_comment = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True)

    # Send log info for debugging
    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    website_link = db.Column(db.String(240))
    facebook_link = db.Column(db.String(240))
    genres = db.Column(db.String(120), nullable=False)
    seeking = db.Column(db.Boolean, default=False)
    seeking_comment = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True)

    # Send log info for debugging
    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False, default=1)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False, default=1)
    date = db.Column(db.DateTime)

    # Send log info for debugging
    def __repr__(self):
      return f'<Show {self.id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  #date = dateutil.parser.parse(value)
  #if format == 'full':
  #    format="EEEE MMMM, d, y 'at' h:mma"
  #elif format == 'medium':
  #    format="EE MM, dd, y h:mma"
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value

  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  List Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  data=[]
  
  locations = (
    db.session.query(Venue)
    .with_entities(Venue.city, Venue.state)
    .filter(Venue.city != "N/A")
    .distinct()
  )

  for location in locations:
    
    location_data = {
      "city": location.city,
      "state": location.state,
      "venues": []
    }

    local_venues = (
      db.session.query(Venue)
      .filter(Venue.city == location.city)
    )
    
    for venue in local_venues:

      shows = (
        db.session.query(Show)
        .filter(Show.venue_id == venue.id)
        .filter(Show.date > datetime.now())
        .count()
      )
      venue_data = {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": shows,
      }

      location_data["venues"].append(venue_data)

    data.append(location_data)

  return render_template('pages/venues.html', areas=data);


#  Search Venues
#  ----------------------------------------------------------------

@app.route('/venues/search', methods=['POST'])
def search_venues():

  response={
    "count": 0,
    "data": []
  }

  search_term = request.form['search_term']

  search_results = (
    db.session.query(Venue)
    .with_entities(Venue.id, Venue.name)
    .filter(Venue.name.ilike(r"%{}%".format(search_term)))
    .filter(Venue.name != 'TBD')
  )

  response['count'] = search_results.count()

  for result in search_results:
    venue_info = {
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": 0,
    }
    response['data'].append(venue_info)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


#  Display Venue
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = (
    db.session.query(Venue)
    .filter(Venue.id == venue_id)
    .first()
  )

  shows_past = []
  shows_upcoming = []

  shows = (
    db.session.query(Show)
    .filter(Show.venue_id == venue_id)
  )

  for show in shows:
    
    show_artist = db.session.query(Artist).filter(Artist.id == show.artist_id).first()
    show_venue = db.session.query(Venue).filter(Venue.id == show.venue_id).first()

    show_info = {
      "artist_id": show_artist.id,
      "artist_name": show_artist.name,
      "artist_image_link": show_artist.image_link,
      "start_time": show.date
    }

    if show.date < datetime.now():
      shows_past.append(show_info)
    else:
      shows_upcoming.append(show_info)

  shows_past_len = len(shows_past)
  shows_upcoming_len = len(shows_upcoming)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(","),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking,
    "seeking_description": venue.seeking_comment,
    "image_link": venue.image_link,
    "past_shows": shows_past,
    "upcoming_shows": shows_upcoming,
    "past_shows_count": shows_past_len,
    "upcoming_shows_count": shows_upcoming_len,
  } 

  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  form = VenueForm(request.form)

  error = False

  try:

    venue = Venue(
      name =              form.name.data,
      city =              form.city.data,
      state =             form.state.data,
      address =           form.address.data, # TODO REMOVE THIS FOR ARTIST
      phone =             form.phone.data,
      genres =            form.genres.data, # TODO fix this
      image_link =        form.image_link.data,
      facebook_link =     form.facebook_link.data,
      website_link =      form.website_link.data,
      seeking =           form.seeking_talent.data, # TODO fix this for artist
      seeking_comment =   form.seeking_description.data
    )

    db.session.add(venue)
    db.session.commit()

    flash('Venue ' + venue.name + ' was successfully listed!')
  except:
    db.session.rollback()
    error=True
    flash('An error occurred. Venue could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    return render_template('pages/home.html')
  else:
    return redirect(url_for('show_venue', venue_id=venue.id))


#  Delete Venue
#  ----------------------------------------------------------------
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  error = False

  venue = Venue.query.filter_by(id=venue_id)



  try:
    venue.delete()
    db.session.commit()
    flash('Venue successfully deleted.')
  except:
    db.session.rollback()
    error = True
    flash('Something went wrong. Make sure there are no Shows pending')
    print('...3')
    print(sys.exc_info())
  finally:
    print('...4')
    db.session.close()
  if error:
    print('There was a problem deleting the venue!!')
    return jsonify({ 'success': False })
  else:
    print('Venue deleted successfully!')
    return jsonify({ 'success': True })


#  Update Venue
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))








#  List Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data=[]

  artists = (
    db.session.query(Artist)
    .filter(Artist.city != "N/A")
  )

  for artist in artists:

    artist_data = {
      "id": artist.id,
      "name": artist.name,
    }

    data.append(artist_data)

  return render_template('pages/artists.html', artists=data)


#  Search Artists
#  ----------------------------------------------------------------

@app.route('/artists/search', methods=['POST'])
def search_artists():

  response={
    "count": 0,
    "data": []
  }

  search_term = request.form['search_term']

  search_results = (
    db.session.query(Artist)
    .with_entities(Artist.id, Artist.name)
    .filter(Artist.name.ilike(r"%{}%".format(search_term)))
    .filter(Artist.name != 'TBD')
  )

  response['count'] = search_results.count()

  for result in search_results:
    artist_info = {
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": 0,
    }
    response['data'].append(artist_info)

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


#  Display Artists
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  artist = (
    db.session.query(Artist)
    .filter(Artist.id == artist_id)
    .first()
  )
  
  shows_past = []
  shows_upcoming = []

  shows = (
    db.session.query(Show)
    .filter(Show.artist_id == artist_id)
  )

  for show in shows:
    
    show_artist = db.session.query(Artist).filter(Artist.id == show.artist_id).first()
    show_venue = db.session.query(Venue).filter(Venue.id == show.venue_id).first()

    show_info = {
      "venue_id": show_artist.id,
      "venue_name": show_artist.name,
      "venue_image_link": show_venue.image_link,
      "start_time": show.date
    }

    if show.date < datetime.now():
      shows_past.append(show_info)
    else:
      shows_upcoming.append(show_info)

  shows_past_len = len(shows_past)
  shows_upcoming_len = len(shows_upcoming)
  
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(","),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking,
    "seeking_description": artist.seeking_comment,
    "image_link": artist.image_link,
    "past_shows": shows_past,
    "upcoming_shows": shows_upcoming,
    "past_shows_count": shows_past_len,
    "upcoming_shows_count": shows_upcoming_len,
  }

  return render_template('pages/show_artist.html', artist=data)


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Delete Artist
#  ----------------------------------------------------------------
@app.route('/artist/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None


#  Update Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))




















#  List Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data = []

  shows = (
    db.session.query(Show)
  )

  for show in shows:

    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)

    show_data = {
      "id": show.id,
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.date
    }

    data.append(show_data)

  return render_template('pages/shows.html', shows=data)


#  Create Shows
#  ----------------------------------------------------------------

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

#  Delete Shows
#  ----------------------------------------------------------------

@app.route('/shows/<show_id>', methods=['DELETE'])
def delete_show(show_id):

  error = False

  show = Show.query.filter_by(id=show_id)

  try:
    show.delete()
    db.session.commit()
    flash('Show successfully deleted.')
  except:
    print('4')
    db.session.rollback()
    error = True
    flash('Something went wrong.')
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    print('There was a problem deleting the show!!')
    return jsonify({ 'success': False })
  else:
    print('Show deleted successfully!')
    return jsonify({ 'success': True })
    

#  Error Handlers
#  ----------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')



#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
