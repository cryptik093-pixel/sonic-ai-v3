#include "omega/Preset.h"
#include "omega/FactoryBank.h"
#include <cstdlib>
#include <iostream>
#include <set>
#define CHECK(x) do {if(!(x)){std::cerr<<"FAIL line "<<__LINE__<<": "<<#x<<'\n';std::exit(1);}}while(false)
int main(){
    std::string error;std::set<std::string> names;
    for(const auto* doc:omega::factoryDocuments){omega::Preset patch;CHECK(omega::parsePreset(doc,patch,error));CHECK(names.insert(patch.name).second);omega::Preset restored;CHECK(omega::parsePreset(omega::exportPreset(patch),restored,error));CHECK(restored.params==patch.params);CHECK(restored.name==patch.name);}
    omega::Preset original;original.name="Keep this";const auto initial=omega::exportPreset(original);
    std::string good=omega::factoryDocuments[0];
    for(size_t length=0;length<good.size();++length){omega::Preset p=original;CHECK(!omega::parsePreset(std::string_view(good).substr(0,length),p,error));CHECK(omega::exportPreset(p)==initial);}
    for(const char* invalid:{"{}","[]","null","{\"schema_version\":NaN}","{\"name\":\"\\uD800\"}","{\"name\":\"\\uDC00\"}","{\"schema_version\":01}","{\"schema_version\":1,\"schema_version\":1}"}){auto p=original;CHECK(!omega::parsePreset(invalid,p,error));CHECK(omega::exportPreset(p)==initial);}
    auto reject=[&](const std::string& from,const std::string& to){auto bad=good;auto pos=bad.find(from);CHECK(pos!=std::string::npos);bad.replace(pos,from.size(),to);auto p=original;CHECK(!omega::parsePreset(bad,p,error));CHECK(omega::exportPreset(p)==initial);};
    auto rejectValue=[&](const std::string& key,const std::string& value){auto prefix="\""+key+"\":";auto pos=good.find(prefix);CHECK(pos!=std::string::npos);pos+=prefix.size();auto end=good.find_first_of(",}",pos);CHECK(end!=std::string::npos);reject(good.substr(pos-prefix.size(),end-pos+prefix.size()),prefix+value);};
    rejectValue("morph","1.1");rejectValue("quality","0.4");reject("\"space\":","\"unknown\":");rejectValue("schema_version","2");rejectValue("morph","true");
    omega::Preset unicode;unicode.name="Glass \xf0\x9f\x8e\xb9";unicode.description="Line\nTwo\t\"quoted\"";omega::Preset decoded;CHECK(omega::parsePreset(omega::exportPreset(unicode),decoded,error));CHECK(decoded.name==unicode.name);CHECK(decoded.description==unicode.description);
    CHECK(!omega::parsePreset(good+" false",decoded,error));CHECK(!omega::parsePreset(std::string(65537,' '),decoded,error));
    std::cout<<"PASS 30 embedded patches, exact JSON roundtrips, truncation, schema rejection and atomic rollback\n";
}
