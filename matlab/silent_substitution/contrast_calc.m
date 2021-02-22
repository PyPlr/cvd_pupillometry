function E = contrast_calc(x, B_primary, B_primary_inputfraction, whichToConsider, whichMode)

% Calculate lmsri
[lmsri1, lmsri2] = predict_lmsri(x, B_primary, B_primary_inputfraction);

switch whichMode
    case 'max'
        E = -(lmsri2(whichToConsider)-lmsri1(whichToConsider))./lmsri1(whichToConsider);
    case 'min'
        E = (lmsri2(whichToConsider)-lmsri1(whichToConsider))./lmsri1(whichToConsider);
end