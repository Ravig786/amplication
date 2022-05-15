import os
import json
from pathlib import Path
from typing import List
import glob
import hashlib
import base64



root_folder=os.getenv('GITHUB_WORKSPACE',Path(__file__).parents[3])
services_output_file=os.getenv('SERVICES_OUPTUT_PATH',os.path.join(root_folder,'service_build_list.json'))
packages_output_file=os.getenv('PACKAGES_OUPTUT_PATH',os.path.join(root_folder,'package_build_list.json'))
hashes_output_file=os.getenv('HASHES_OUPTUT_PATH',os.path.join(root_folder,'hashes.json'))
services_retag_output_file=os.getenv('SERVICES_RETAG_OUPTUT_PATH',os.path.join(root_folder,'service_retag_list.json'))
helm_services_folder=os.getenv('HELM_SERVICES_FOLDER',os.path.join(root_folder,'helm/charts/services'))
packages_folder=os.getenv('PACKAGES_FOLDER',os.path.join(root_folder,'packages'))
changed_folders=[]
#changed_folders=["amplication-cli", "amplication-client", "amplication-container-builder", "amplication-data", "amplication-data-service-generator", "amplication-deployer", "amplication-design-system", "amplication-scheduler", "amplication-server"]
changed_files=os.getenv('CHANGED_FILES_PR') or os.getenv('CHANGED_FILES_NOT_PR')

package_build_list=[]
service_build_list=dict()
service_retag_list=dict()

print(f"root_folder: {root_folder}")
print(f"services_output_file: {services_output_file}")
print(f"packages_output_file: {packages_output_file}")
print(f"helm_services_folder: {helm_services_folder}")
print(f"packages_folder: {packages_folder}")
print(f"changed_files: {changed_files}")

def is_service(service_list,service_name) -> bool:
  return service_name in service_list

def dependet_services(package_name,dict) -> List[str]:
    npm_package_name=package_name.replace("-","/",1)
    for service in all_services:
        package_json=f"{packages_folder}/{service}/package.json"
        with open(package_json, 'r') as file:
            depencies = file.read().replace('\n', '')
        if f"\"@{npm_package_name}\":" in depencies:
            print(f"The service {service} depends on package {npm_package_name}, will build")
            if service not in dict:
                dict[service]=[service,package_name]
            else: 
                dict[service]+=[package_name]

def get_changed_folders():
    if not changed_files:
        print('no changed files')
    else:
        for changed_file in changed_files.split(','):
            changed_folders.append(changed_file.split('/')[1])
    print(f"changed_folders: {changed_folders}")
    return changed_folders

def get_package_name(raw_package) -> str:
    fixed_package = f"@{raw_package.replace('-','/',1)}"
    print(f"package name was fixed from {raw_package} to {fixed_package}")
    return fixed_package

def get_hashes(folders_list) -> dict():
    hashes=dict()
    for folders_to_hash in folders_list.keys():
        hash_=""
        filenames=[]
        for folder_to_hash in folders_list[folders_to_hash]:
            path=os.path.join(packages_folder,folder_to_hash,'**/*')
            filenames.append(glob.glob(path))
        for filename in filenames:
            with open(filename[0], 'rb') as inputfile:
                data = inputfile.read()
                hash_+=hashlib.md5(data).hexdigest()
        hashes[folder_to_hash]=str(int(hashlib.sha256(hash_.encode('utf-8')).hexdigest(), 16))
    return hashes

changed_folders = get_changed_folders()
service_build_list=dict()
all_services=os.listdir(helm_services_folder)
for changed_folder in changed_folders:
    if is_service(all_services,changed_folder):
        if changed_folder not in service_build_list:
            service_build_list[changed_folder] = [changed_folder]
    else:
        dependet_services(changed_folder,service_build_list)
    if get_package_name(changed_folder) not in package_build_list:
        package_build_list.append(get_package_name(changed_folder))
    for service_name in all_services:
        if service_name not in service_build_list:
            service_retag_list[changed_folder] = [changed_folder]
            dependet_services(changed_folder,service_retag_list)

final_services_list=dict()

hashes=get_hashes(service_build_list.update(service_retag_list))
final_services_list.update(service_build_list)
final_services_list.update(service_retag_list)
get_hashes(final_services_list)
# for folders_to_hash in service_build_list.keys():
#     hash_=""
#     filenames=[]
#     for folder_to_hash in service_build_list[folders_to_hash]:
#         path=os.path.join(packages_folder,folder_to_hash,'**/*')
#         filenames.append(glob.glob(path))
#     for filename in filenames:
#         with open(filename[0], 'rb') as inputfile:
#             data = inputfile.read()
#             hash_+=hashlib.md5(data).hexdigest()
#     hashes[folders_to_hash]=str(int(hashlib.sha256(hash_.encode('utf-8')).hexdigest(), 16))



print(f"Will create the hashes file: {hashes}")
hashes_b64 = base64.b64encode(json.dumps(hashes).encode('ascii'))
f = open(hashes_output_file, "w")
f.write(str(hashes_b64).replace("b\'","").replace("\'",""))
f.close()



print(f"Will build the follwoing services: {service_build_list}")
with open(services_output_file, 'w') as outfile:
    service_build_list_fixed = json.dumps(list(service_build_list.keys()))
    json.dump(service_build_list_fixed, outfile)
print(f"Will build the follwoing pcakges: {package_build_list}")
with open(packages_output_file, 'w', encoding='utf-8') as outfile:
    package_build_list_fixed = json.dumps(package_build_list)
    json.dump(package_build_list_fixed, outfile, ensure_ascii=False, indent=4)
print(f"Will retag the follwoing pcakges: {service_retag_list}")
with open(services_retag_output_file, 'w', encoding='utf-8') as outfile:
    services_retag_list_fixed = json.dumps(service_retag_list)
    json.dump(services_retag_list_fixed, outfile, ensure_ascii=False, indent=4)    
