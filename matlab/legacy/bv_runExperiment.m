%% Set up exam-level characteristics
ageInYears = 42;
subjID = 'test';

%% PIPR
protocolID = 'pipr';
bv_runPupilProtocol(protocolID,subjID, ageInYears)

%% LMS
protocolID = 'lms';
bv_runPupilProtocol(protocolID, subjID, ageInYears)

%% Mel
protocolID = 'mel';
bv_runPupilProtocol(protocolID, subjID, ageInYears)