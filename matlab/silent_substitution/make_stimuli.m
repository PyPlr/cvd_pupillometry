% Housekeeping
clearvars;
addpath(genpath(pwd));

%% Get the primaries

% Load the alpha-opic irradiances
M = readtable('stlab_alphaopic.csv');

% Get the radiances
alphaOpicRadiances = [M.L M.M M.S M.Rods M.Mel];


NPrimaries = 10;
for ii = 1:NPrimaries
    % Get the indices for that LED
    idx = (M.led+1 == ii);
    
    B_primary{ii} = alphaOpicRadiances(idx, :);
    B_primary_inputfraction = M.intensity(idx, :)/4095;
end

%% LMSToXYZ
M_LMSRIToXYZ = [1.93986443 1.34664359 0.43044935 0 0; ...
    0.69283932 0.34967567 0 0 0 ; ...
    0 0 2.14687945 0 0];
M_LMSToXYZ = M_LMSRIToXYZ(:, 1:3);
M_XYZToLMS = inv(M_LMSToXYZ);

%%

%%

% Set up an optimization which minimizes the difference to a given
% tristimulus value while maximizing melanopsin contrast
NPrimaries = 10;
x0 = 0.5*ones(NPrimaries, 1);

% Set lower and upper bounds
headroom = 1/4095;
lb0 = headroom*ones(NPrimaries, 1);
ub0 = ones(NPrimaries, 1)-headroom;

%% Define the possible combos
whichToStimulate = 5; % Mel
whichToMatch = [1 2 3]; % SML cones

% Set up some bounds
lb = lb0; ub = ub0;

problem = createOptimProblem('fmincon',...
    'objective', @(x)contrast_calc(x, B_primary, B_primary_inputfraction, whichToStimulate, 'max'),...
    'x0', [x0 ; x0], 'lb', [lb ; lb], 'ub', [ub ; ub], ...
    'nonlcon', @(x)nlconstraint_ss(x, B_primary, B_primary_inputfraction, whichToMatch, 'zero'), ...
    'options', optimoptions(@fmincon,'Algorithm','sqp','Display','iter','TolConSQP',1e-4));
gs = GlobalSearch('Display', 'on', 'NumTrialPoints', 1000);
[xs,fval] = run(gs,problem);

% Extract the values for scene 1 (1:10) and scene 2 (11:20)
set1 = xs(1:10);
set2 = xs(11:20);

% Get the primaries
[smlri1, smlri2] = predict_lmsri(xs, B_primary, B_primary_inputfraction)

%% Extract the values
xs = round(xs*4095)
set1 = xs(1:10);
set2 = xs(11:20);

%% Calculate
spd = (csvread('corrected_oo_spectra.csv', 1, 2))

% Load CIE 1931
load T_xyz1931
T_xyz = SplineCmf(S_xyz1931, 683*T_xyz1931, [380 1 401]);

%% TO DO: Titrate between min and max.