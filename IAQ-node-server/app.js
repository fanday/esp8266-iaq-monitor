const Influx = require('influx')
const influx = new Influx.InfluxDB({
  host: 'localhost',
  port: 8086,
  database: 'test',
  username:'fanday',
  password:'password',
  schema: [
    {
      measurement: 'iaq',
      fields: {
        temperature: Influx.FieldType.INTEGER,
        humidity: Influx.FieldType.INTEGER,
        voc:Influx.FieldType.FLOAT
      },
      tags: [
        'IAQ'
      ]
    }
  ]
})

var net = require('net');
var IAQServer = net.createServer();
IAQServer.on('connection', function(client){
  console.log('client connected!');
  client.on('data', function(data){
    console.log(data);
    iaqData = JSON.parse(data);
    console.log(iaqData);
    datastreams = iaqData['datastreams'];
    console.log('datastreams:', datastreams);

    var tmp = 0;
    var voc = 0.0;
    var hum = 0;
    datastreams.forEach(function(d){
      console.log('d:',d);
      val = d['datapoints'][0]['value'];
      if(d['id'] == 'temperature'){
        tmp = val;
      }

      if(d['id'] == 'humidity'){
        hum = val;
      }

      if(d['id'] == 'voc'){
        voc = val;
      }
    });
    console.log('temperature:', tmp, 'humidity:', hum,'voc:', voc)
    influx.writePoints([
      {
        measurement: 'iaq',
        fields: { temperature:tmp, humidity: hum, voc:voc },
      }
    ]).catch(err => {
      console.error(`Error saving data to InfluxDB! ${err.stack}`);
    });
    client.end();
  });
});
IAQServer.listen(9000);
