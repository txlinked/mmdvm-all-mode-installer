#include <cstdio>
#include <cstring>
#include <vector>
#include <array>
#include "RingBuffer.h"
#define private public
#include "ModeConv.h"
#undef private
int main(){
 CModeConv seed,forward,back;
 for(unsigned i=0;i<120;i++)seed.putAMBE2DMR((i*31+7)&4095,(i*43+19)&4095,(i*97531+4567)&33554431);
 std::vector<std::array<unsigned char,33>> original;
 for(unsigned i=0;i<40;i++){std::array<unsigned char,33> d{};seed.getDMR(d.data());original.push_back(d);forward.putDMR(d.data());}
 for(unsigned i=0;i<24;i++){unsigned char y[120]={};forward.getYSF(y);back.putYSF(y);}
 unsigned errors=0;
 for(unsigned i=0;i<40;i++){unsigned char d[33]={};back.getDMR(d);for(unsigned bit=0;bit<264;bit++){if(bit>=108&&bit<156)continue;unsigned mask=128>>(bit%8);if((d[bit/8]&mask)!=(original[i][bit/8]&mask))errors++;}}
 printf("DMR -> YSF -> DMR: 120 AMBE frames, %u differing voice bits\n",errors);return errors?1:0;
}
