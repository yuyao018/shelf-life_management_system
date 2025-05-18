export default {
	reject_buttonOnClick () {
		reject_request.run()
		setInterval(5)
		get_all_data_admin.run()
		setInterval(5)
		get_approval_status.run()
	}
}