function bv_runPupilProtocol(protocolID, subjID, ageInYears)
% Clear command window
clc;

% Load stimuli
tmp = load('stimuli20190610.mat');

% Figure out the correct age bracket
refAge = [25:5:70];
[~, ageIdx] = min(abs(ageInYears-refAge));

% Load the correct stimuli
switch protocolID
    case 'pipr'
        bgPrimary = bv_primariesToSettings(tmp.stimuli{ageIdx}.pipr.zeroSetting);
        modPrimaryShortWl = bv_primariesToSettings(tmp.stimuli{ageIdx}.pipr.shortWlSetting);
        modPrimaryLongWl = bv_primariesToSettings(tmp.stimuli{ageIdx}.pipr.longWlSetting);
        
        % Counter balanced sequence, generated with bv_mseq:
        % >> ms = bv_mseq(2,4,3,1)
        % -1 -> 2
        % And added a wrap around to the beginning
        
        order = [2 1 1 2 2 1 2 2 2 1 1 1 1 2 1 2]; % Must be same as trials below
        runID = '01';
    case 'lms'
        bgPrimary = bv_primariesToSettings(tmp.stimuli{ageIdx}.lms.solution.spec.bgPrimary);
        modPrimary = bv_primariesToSettings(tmp.stimuli{ageIdx}.lms.solution.spec.modPrimary);
        runID = '02';
    case 'mel'
        bgPrimary = bv_primariesToSettings(tmp.stimuli{ageIdx}.mel.solution.spec.bgPrimary);
        modPrimary = bv_primariesToSettings(tmp.stimuli{ageIdx}.mel.solution.spec.modPrimary);
        runID = '03';
end

try
    % Set up device
    fprintf('*** Initialising device ***\n');
    dev = bv_setupDevice();
    fprintf('--- Done. --- \n\n');
    commandwindow;
    % Set to background for orientation
    input(sprintf('*** <strong>Turn on the light for orientation?</strong> (Press enter) ***\n'));
    bv_setSettings(dev, bgPrimary);
    
    fprintf('*** Switch to Pupil Capture and enter the subject details ***\n');
    fprintf('    <strong>%s_%s</strong>\n', subjID, runID)
    input(sprintf('--- <strong>Have you started the pupil recording in Pupil Capture? Press Enter to confirm.</strong> ---\n'));
    bv_setSettings(dev, bgPrimary);
    
    fprintf('>>> Starting protocol <strong>%s</strong> <<<\n', protocolID);
    
    input(sprintf('*** Start <strong>background</strong> period (4min 30sec) (Press enter) ***'));
    bv_setSettings(dev, bgPrimary);
    fprintf('... Showing background for adaptation ...\n');
    tic;
    pause(4.5*60);
    toc
    fprintf('*** --- Ending <strong>background</strong> ---\n');
    
    % Go through trials
    NTrials = 16;
    ii = 1;
    while ii <= NTrials
        % Special PIPR case
        if strcmp(protocolID, 'pipr')
            switch order(ii)
                case 1
                    modPrimary = modPrimaryShortWl;
                case 2
                    modPrimary = modPrimaryLongWl;
            end
        end
        
        bv_setSettings(dev, bgPrimary);
        input(sprintf('*** Next trial (trial %g)? (Press Enter) ***', ii));
        fprintf('--- Starting <strong>trial %g</strong> ---\n', ii);
        pause(5);
        fprintf('... Showing stimulus ...\n');
        bv_setSettings(dev, modPrimary);
        pause(5);
        bv_setSettings(dev, bgPrimary);
        pause(15);
        fprintf('--- Ending <strong>trial %g</strong> ---\n\n', ii);
        
        whichResponse = bv_proceedDialogue;
        switch whichResponse
            case 1
                ii = ii+1;
            case 3
                fprintf('--- Ending protocol %s prematurely---\n', protocolID);
                break;
        end
    end
    fprintf('--- Ending protocol %s ---\n', protocolID);
catch 
    bv_turnAllOff;
end