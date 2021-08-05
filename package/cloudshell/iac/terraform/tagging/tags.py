class TagsManager:
    class DefaultTagNames:
        created_by = "CreatedBy"
        owner = "Owner"
        blueprint = "Blueprint"
        sandbox_id = "SandboxId"
        domain = "Domain"
        ran_by = "RanBy"

    class DefaultTagValues:
        created_by = "CloudShell"

    def __init__(self, reservation_info):
        """Init command.

        :param reservation_info:
        """
        self._reservation_info = reservation_info

    def get_default_tags(self):
        """Get pre-defined CloudShell tags.

        :return:
        """
        return {
            self.DefaultTagNames.created_by: self.DefaultTagValues.created_by,
            self.DefaultTagNames.owner: self._reservation_info.owner_user,
            self.DefaultTagNames.blueprint: self._reservation_info.environment_name,
            self.DefaultTagNames.sandbox_id: self._reservation_info.reservation_id,
            self.DefaultTagNames.domain: self._reservation_info.domain,
            self.DefaultTagNames.ran_by: self._reservation_info.running_user,
        }
