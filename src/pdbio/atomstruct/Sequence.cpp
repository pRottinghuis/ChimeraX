// vim: set expandtab ts=4 sw=4:
#include "Sequence.h"

Sequence::_1Letter_Map Sequence::_nucleic3to1 = {
        {"A", 'A'},
        {"+A", 'A'},
        {"ADE", 'A'},
        {"DA", 'A'},
        {"C", 'C'},
        {"+C", 'C'},
        {"CYT", 'C'},
        {"DC", 'C'},
        {"G", 'G'},
        {"+G", 'G'},
        {"GUA", 'G'},
        {"DG", 'G'},
        {"T", 'T'},
        {"+T", 'T'},
        {"THY", 'T'},
        {"DT", 'T'},
        {"U", 'U'},
        {"+U", 'U'},
        {"URA", 'U'}
};
Sequence::_1Letter_Map Sequence::_protein3to1 = {
        {"ALA", 'A'},
        {"ARG", 'R'},
        {"ASH", 'D'}, // Amber (protonated ASP)
        {"ASN", 'N'},
        {"ASP", 'D'},
        {"ASX", 'B'}, // ambiguous ASP/ASN
        {"CYS", 'C'},
        {"CYX", 'C'}, // Amber (disulphide)
        {"GLH", 'E'}, // Amber (protonated GLU)
        {"GLU", 'E'},
        {"GLN", 'Q'},
        {"GLX", 'Z'}, // ambiguous GLU/GLN
        {"GLY", 'G'},
        {"HID", 'H'}, // Amber (delta protonated)
        {"HIE", 'H'}, // Amber (epsilon protonated)
        {"HIP", 'H'}, // Amber (doubly protonated)
        {"HIS", 'H'},
        {"HYP", 'P'}, // hydroxyproline, which in theory
            // has its own letter ('O') but using that is problematic
            // with similarity matrices
        {"ILE", 'I'},
        {"LEU", 'L'},
        {"LYS", 'K'},
        {"MET", 'M'},
        {"MSE", 'M'}, // Selenomethionine
        {"PHE", 'F'},
        {"PRO", 'P'},
        {"SER", 'S'},
        {"THR", 'T'},
        {"TRP", 'W'},
        {"TYR", 'Y'},
        {"VAL", 'V'}
};
Sequence::_1Letter_Map Sequence::_rname3to1;

unsigned char
Sequence::nucleic3to1(const std::string& rn)
{
    _1Letter_Map::const_iterator l1i = _nucleic3to1.find(rn);
    if (l1i == _nucleic3to1.end()) {
        return 'X';
    }
    return (*l1i).second;
}

unsigned char
Sequence::protein3to1(const std::string& rn)
{
    _1Letter_Map::const_iterator l1i = _protein3to1.find(rn);
    if (l1i == _protein3to1.end()) {
        return 'X';
    }
    return (*l1i).second;
}

void
Sequence::_init_rname_map()
{
    for (auto mapping : Sequence::_nucleic3to1) {
        Sequence::_rname3to1[mapping.first] = mapping.second;
    }
    for (auto mapping : Sequence::_protein3to1) {
        Sequence::_rname3to1[mapping.first] = mapping.second;
    }
}

unsigned char
Sequence::rname3to1(const std::string& rn)
{
    if (_rname3to1.empty())
        _init_rname_map();

    _1Letter_Map::const_iterator l1i = _rname3to1.find(rn);
    if (l1i == _rname3to1.end()) {
        return 'X';
    }
    return (*l1i).second;
}
