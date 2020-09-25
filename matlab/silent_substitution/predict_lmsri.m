function [smlri1, smlri2] = predict_slmri(x, B_primary, B_primary_inputfraction)

% Predict the signal
set1 = x(1:10);
set2 = x(11:20);

smlri1 = 0;
smlri2 = 0;
for ii = 1:10
    smlri1 = smlri1 + interp1(B_primary_inputfraction, B_primary{ii}, set1(ii));
    smlri2 = smlri2 + interp1(B_primary_inputfraction, B_primary{ii}, set2(ii));
end