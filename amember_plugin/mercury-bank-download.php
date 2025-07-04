<?php
/**
 * Mercury-bank-download Integration Plugin
 * Checklist (mark tested items with x):
 * [x] - template generated
 * [ ] - go to aMember Cp -> Setup -> Plugins and enable this plugin
 * [ ] - test user creation
 *       try to create user in aMember and add access manually.
 *       Login to Mercury-bank-download and check that
 *       that corresponding user appeared in users list and all necessary
 *       fields transferred
 * [ ] - test password generation: login to mercury-bank-download as the new user
 * [ ] - update user record in amember and try to login and view profile in the script
 * [ ] - implement single-login
 *
 **/
class Am_Protect_MercuryBankDownload extends Am_Protect_Databased
{
    const PLUGIN_DATE = '$Date$';
    const PLUGIN_REVISION = '1.0.0';

    protected $guessTablePattern = "users";
    protected $guessFieldsPattern = [
        'username','email','password_hash','first_name','last_name','is_active',    ];
    protected $groupMode = Am_Protect_Databased::GROUP_MULTI;

    public function afterAddConfigItems($form)
    {
        parent::afterAddConfigItems($form);
        // additional configuration items for the plugin may be inserted here
    }

    public function getPasswordFormat()
    {
        return SavedPassTable::PASSWORD_PHPASS;
    }

    /**
     * Return record of customer currently logged-in to the
     * third-party script, or null if not found or not logged-in
     * @return Am_Record|null
     */
    public function getLoggedInRecord()
    {
        // for single-login must return
    }

    public function loginUser(Am_Record $record, $password)
    {
        // login user to third-party script
    }

    public function logoutUser(User $user)
    {
        // logout user from third-party script
    }

    public function createTable()
    {
        $table = new Am_Protect_Table($this, $this->getDb(), '?_users', 'id');
        $table->setFieldsMapping([
            [Am_Protect_Table::FIELD_LOGIN, 'username'],
            [Am_Protect_Table::FIELD_EMAIL, 'email'],
            [Am_Protect_Table::FIELD_PASS, 'password_hash'],
            [Am_Protect_Table::FIELD_NAME_F, 'first_name'],
            [Am_Protect_Table::FIELD_NAME_L, 'last_name'],
            [':1', 'is_active'],
        ]);
        
        $table->setGroupsTableConfig([
            Am_Protect_Table::GROUP_TABLE => '?_user_roles',
            Am_Protect_Table::GROUP_GID => 'role_id',
            Am_Protect_Table::GROUP_UID => 'user_id',
        ]);
        
        return $table;
    }

    public function getAvailableUserGroupsSql()
    {
        return "SELECT
            id as id,
            name as title,
            NULL as is_banned, #must be customized
            NULL as is_admin # must be customized
            FROM ?_roles";
    }

    function getReadme()
    {
        return <<<CUT
    mercury-bank-download README
    This plugin is for the mercury-bank-download package at https://www.github.com/kumpeapps/mercury-bank-download

CUT;
    }
}