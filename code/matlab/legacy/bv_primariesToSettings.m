function settings = bv_primariesToSettings(primaries)
if any(primaries > 1)
    error('Primaries out of bounds (larger than 1)');
end
if any(primaries < 0)
    error('Primaries out of bounds (smaller than 0)');
end
settings = round(primaries*4095);