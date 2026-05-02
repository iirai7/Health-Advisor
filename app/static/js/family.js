/**
 * family.js
 * Handles family member management (fetch, add, delete).
 *
 * Depends on: api.js, translation.js
 * Exposes: global `Family` object
 */

const Family = (function () {

    // ─────────────────────────────────────────
    // PUBLIC: getMembers()
    // Fetch all family members for the current user.
    // Returns { success, members: [] }
    // ─────────────────────────────────────────
    async function getMembers() {
        try {
            const result = await API.get('/api/family/');

            if (!result.success) {
                console.error('[Family.getMembers]', result.message);
                return { success: false, members: [] };
            }

            // The backend returns the list in result.data
            return { 
                success: true, 
                members: result.data || [] 
            };

        } catch (err) {
            console.error('[Family.getMembers]', err);
            return { success: false, members: [] };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: addMember({ name, email, relation, phone })
    // Add a new family member account.
    // Returns { success, message, member_id }
    // ─────────────────────────────────────────
    async function addMember({ name, email, relation, phone }) {
        try {
            const result = await API.post('/api/family/add', {
                name,
                email,
                relation,
                phone_number: phone
            });

            if (!result.success) {
                console.error('[Family.addMember]', result.message);
                return { 
                    success: false, 
                    message: result.message || t('common.error') 
                };
            }

            return { 
                success: true, 
                message: result.message || t('common.success'),
                member_id: result.member_id
            };

        } catch (err) {
            console.error('[Family.addMember]', err);
            return { 
                success: false, 
                message: t('common.error') 
            };
        }
    }


    // ─────────────────────────────────────────
    // PUBLIC: deleteMember(memberId)
    // Delete a family member account.
    // Returns { success, message }
    // ─────────────────────────────────────────
    async function deleteMember(memberId) {
        try {
            const result = await API.delete(`/api/family/${memberId}`);

            if (!result.success) {
                console.error('[Family.deleteMember]', result.message);
                return { 
                    success: false, 
                    message: result.message || t('common.error') 
                };
            }

            return { 
                success: true, 
                message: result.message || t('common.success') 
            };

        } catch (err) {
            console.error('[Family.deleteMember]', err);
            return { 
                success: false, 
                message: t('common.error') 
            };
        }
    }


    // ─────────────────────────────────────────
    // EXPOSE
    // ─────────────────────────────────────────
    return {
        getMembers,
        addMember,
        deleteMember
    };

})();