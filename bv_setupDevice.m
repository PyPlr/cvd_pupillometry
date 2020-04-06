function dev = lightmotif_setupDevice

url_module = 'http://192.168.7.2:8181';
device_id = 1;
url = [url_module, '/api/login'];
information = struct();
information.username = 'admin';
information.password = '83e47941d9e930f6'; % BVUK
data = savejson('',information);
headers = struct('name', {'content-type','accept'}, 'value', {'application/json','*/*'});
[~, extras] = urlread2(url, 'POST', data, headers);
pause(0.5);
cookie = strsplit(char(extras.allHeaders.set_cookie), ';');
opts = weboptions('KeyName','Cookie','KeyValue',char(cookie(1)));

dev.url_module = url_module;
dev.device_id = device_id;
dev.opts = opts;
