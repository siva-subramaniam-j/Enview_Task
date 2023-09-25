from flask import Flask, request, jsonify
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import pytz
from flask_ngrok import run_with_ngrok


global alert_idd
app = Flask(__name__)
run_with_ngrok(app)


alert_idd=1
utc=pytz.UTC
# In-memory data structures
events = []  # List to store driving events
alerts = []  # List to store generated alerts
location_type_thresholds = {
    'highway': 4,
    'city_center': 3,
    'commercial': 2,
    'residential': 1
}

location_dict={}                               # We will be storing different types of location whose values will be dictionary of vechicles , whose values will be the count of events
def generate_alert(eventlis):
    
   
    for i in eventlis:
        location=i['location_type']    #appending new location with the vechicle details
       
        
        if (location) not in location_dict.keys():
            
            location_dict[location]={i.get('vehicle_id'):1}
            
        if location in location_dict.keys():
            vehicle_id=i.get('vehicle_id')                      # appending only vechicle if location already exists
            
            if vehicle_id not in location_dict.get(location).keys(): 
                location_dict[location][vehicle_id]=1           # updating the five minutes of alerts details  in the dictionary 
                
            location_dict[location][vehicle_id]+=1
    
    for location in location_dict.keys():
        
        for vehicle in location_dict[location].keys():
            if location_dict[location][vehicle]>=location_type_thresholds.get(location):  #checking the count is more than the threshold of the location
                
                current_time=datetime.datetime.now()
                time_threshold=current_time-datetime.timedelta(minutes=5)
                print(time_threshold)
                recent_alerts = [a for a in alerts if ((datetime.datetime.fromisoformat(a['timestamp']).replace(tzinfo=utc)>= datetime.datetime.fromisoformat(time_threshold.isoformat()).replace(tzinfo=utc))
and a['vehicle_id']!=str(vehicle) and a['location_type']!=str(location))]
                
                
                global alert_idd
                if not recent_alerts:
                    alert={ 'alert_id': alert_idd,
                                'timestamp':current_time.isoformat(),
                                'location_type':location,
                                'vehicle_id':vehicle}
                    alert_idd+=1
                    alerts.append(alert)
                    print('alert sent')

    return(alerts)
                
            
            
            

       
            
            
    
def evaluate_rule():
    # Function to periodically evaluate the rule
    current_time = datetime.datetime.now()
    time_threshold = current_time - datetime.timedelta(minutes=5)
    
    # Filter events within the last 5 minutes
    recent_events = [e for e in events if datetime.datetime.fromisoformat(e['timestamp']).replace(tzinfo=utc)  >= datetime.datetime.fromisoformat(time_threshold.isoformat()).replace(tzinfo=utc)]
    
    # Evaluate the rule for each recent event
    generate_alert(recent_events)



@app.route('/event', methods=['POST'])
def receive_event():
    
    data = request.get_json()
    events.append(data)
           
    return jsonify({"message": "Event received and stored."}), 200

@app.route('/alert/<string:alert_id>', methods=['GET'])
def get_alert(alert_id):
    
    alert = next((a for a in alerts if a['alert_id'] == int(alert_id)), None)
   
    if alert:
        return jsonify(alert)
    else:
        return jsonify({"message": "Alert not found."}), 404
    
scheduler = BackgroundScheduler()     #Initializing Schedular to check for rule

if __name__ == '__main__':
    scheduler.add_job(evaluate_rule, 'interval', minutes=5)
    scheduler.start()
    a=threading.Thread(target=lambda: app.run()).start()
