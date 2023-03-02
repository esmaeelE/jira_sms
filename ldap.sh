###
### Query ldap server to get user information and store it to text file, user.txt
###


ldapsearch -x -b "cn=users,dc=bonyan,dc=local" -H ldap://ad.bonyan.local:3268 -D "bonyan\sms" -s sub "(&(objectCategory=Person)(sAMAccountName=*)(memberOf=CN=Jira Users,CN=Users,DC=bonyan,DC=local))" sAMAccountName telephoneNumber mail name -w "Bonyan@123" | head -n -7 | awk 'BEGIN{FS=": *"; OFS=","}
     (NF==0) { print sAMAccountName,name,telephoneNumber,mail }
     (NF==0) { mail = sAMAccountName = name = cn = ""; next }
     {split($0,a,": ")}
     /^mail:/{mail=a[2]}
     /^sAMAccountName:/{sAMAccountName=a[2]}
     /^name:/{name=a[2]}
     /^telephoneNumber/{telephoneNumber=a[2]}
     END{ print sAMAccountName,name,telephoneNumber,mail }' | tail -n +2 > user.txt

