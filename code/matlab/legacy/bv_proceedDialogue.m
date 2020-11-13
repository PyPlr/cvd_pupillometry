function whichResponse = bv_proceedDialogue

validChoice = false;
while ~validChoice
    theChoice = input(sprintf('>>> Accept trial [<strong>a</strong>], repeat trial [<strong>r</strong>], or end block [<strong>e</strong>]? '), 's');
    switch theChoice
        case {'a' 'A'}
            whichResponse = 1;
            validChoice = true;
        case {'r' 'R'}
            whichResponse = 2;
            validChoice = true;
        case {'e' 'E'}
            whichResponse = 3;
            validChoice = true;
        otherwise
            fprintf('*** <strong>Invalid choice!</strong>\n');
    end
end