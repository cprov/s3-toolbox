#!/bin/bash
#
# Iterates over tenants associated with the logged in identity and checks Turia IAM status.
#
# Ensure you have the MGCCLI and YQ dependencies installed before running this script:
#
#   sudo snap install mgccli yq
#


# Who doesn't like colors and emojis in bash, right ?
RED="\033[1;31m🚨"
GRE="\033[1;32m✅"
YEL="\033[1;33m😵"
BLU="\033[1;34m🔎"
ESC="\033[0m"


for id in $(mgc auth tenant list -r | yq '.[] | .uuid'); do
    echo -e "$BLU Checking Tenant ID: $id$ESC"
    mgc auth tenant set $id --no-confirm > /dev/null

    CURRENT=$(mgc auth tenant current -r)
    is_managed=$(echo -en "$CURRENT" | yq '. | .is_managed')
    if [[ "$is_managed" == "false" ]]; then
	echo -e "\t$YEL This tenant is NOT an organization.$ESC"
    else
	name=$(echo -en "$CURRENT" | yq '. | .legal_name')
	echo -e "\t$GRE Found organization: $name$ESC"

	# Check if Turia IAM was activated.
	# XXX 20250901 cprov: IAM API returns an ugly 404 until activation.
	IGNORED=$(mgc iam access-control list -r 2>&1 > /dev/null)
	if [[ "$?" -eq 0 ]]; then
	    echo -e "\t$GRE Turia IAM was activated.$ESC"
	    IAM=$(mgc iam access-control list -r)

	    # Check if RBAC is enabled.
	    ENABLED=$(echo -en "$IAM" | yq '. | .enabled')
	    if [[ "$ENABLED" == "true" ]]; then
		echo -e "\t$GRE Turia IAM is ENABLED.$ESC"
	    else
		echo -e "\t$RED Turia IAM is DISABLED.$ESC"
	    fi

	    # Check if MFA is enforced
	    ENFORCE_MFA=$(echo -en "$IAM" | yq '. | .enforce_mfa')
	    if [[ "$ENFORCE_MFA" == "true" ]]; then
		echo -e "\t$GRE MFA IS enforced.$ESC"
	    else
		echo -e "\t$RED MFA IS NOT enforced.$ESC"
	    fi
	else
	    echo -e "\t$RED Turia IAM NEEDS activation.$ESC"
	fi
    fi

    IC_NETS_REGEX="^(10\.124|10\.175|10\.139|10\.136|10\.173|10\.125|10\.140).*"

    SE1_VPC_ID=$(mgc network vpcs list --region br-se1 -r | yq '.vpcs[0] | .id' -r)
    SE1_IC_NETS=$(mgc network vpcs subnets list ${SE1_VPC_ID} --region br-se1 -r | yq '.subnets[] | select(.ip_version = "IPv4") | .["cidr_block"]' -r | grep -E "$IC_NETS_REGEX" | xargs)
    if [ -n "$SE1_IC_NETS" ]; then
	echo -e "\t$YEL BR-SE1 HAS MAGALU interconnect: $SE1_IC_NETS"
    else
	echo -e "\t$GRE BR-SE1 NOT connected to MAGALU"
    fi

    NE1_VPC_ID=$(mgc network vpcs list --region br-ne1 -r | yq '.vpcs[0] | .id' -r)
    NE1_IC_NETS=$(mgc network vpcs subnets list ${NE1_VPC_ID} --region br-ne1 -r | yq '.subnets[] | select(.ip_version = "IPv4") | .["cidr_block"]' -r | grep -E "$IC_NETS_REGEX" | xargs)
    if [ -n "$NE1_IC_NETS" ]; then
	echo -e "\t$YEL BR-NE1 HAS MAGALU interconnect: $NE1_IC_NETS"
    else
	echo -e "\t$GRE BR-NE1 NOT connected to MAGALU"
    fi


done
