function bv_setSettings(dev, primaries)

theSpecString = sprintf('%d,', primaries);
theSpecString(end) = '';

webread([dev.url_module,'/api/luminaire/', num2str(dev.device_id), '/spectruma/' theSpecString], dev.opts);
