export default {
	logout_buttononClick () {
		removeValue('name');
		removeValue('email');
  	removeValue('user_role');
  	navigateTo('Login', { replace: true });
		showAlert("Logout Successful!", "success");
	}
}