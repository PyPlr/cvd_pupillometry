function [c, ceq] = nlconstraint_ss(x, B_primary, B_primary_inputfraction, whichToConsider, whichMode)

% Calculate SMLRI
[smlri1, smlri2] = predict_lmsri(x, B_primary, B_primary_inputfraction);

switch whichMode
    case 'zero'
        ceq = (smlri2(whichToConsider)-smlri1(whichToConsider))./smlri1(whichToConsider);
    case 'targetXYZ'
        % Wrong, need to update
        %ceq = (smlri2(whichToConsider)-smlri1(whichToConsider))./smlri1(whichToConsider);
end
c = [];